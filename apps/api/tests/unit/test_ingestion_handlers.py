"""Ingestion handlers against in-memory ports: upload and duplicates, re-parse, meta, delete, the pipeline, AI models and
processing defaults (ADR-02)."""
import hashlib
import json
import uuid

import pytest

from app.modules.ingestion.application.api import MODEL_TIMEOUT_SECONDS, IngestionApi
from app.modules.ingestion.application.commands.delete_document import DeleteDocument, DeleteDocumentHandler
from app.modules.ingestion.application.commands.ingest_document import IngestDocument, IngestDocumentHandler, MarkIngestFailed, MarkIngestFailedHandler
from app.modules.ingestion.application.commands.reparse_document import ReparseDocument, ReparseDocumentHandler
from app.modules.ingestion.application.commands.save_ai_model import CreateAiModel, CreateAiModelHandler, UpdateAiModel, UpdateAiModelHandler
from app.modules.ingestion.application.commands.save_ingestion_settings import SaveIngestionSettings, SaveIngestionSettingsHandler
from app.modules.ingestion.application.commands.store_asset import StoreImage
from app.modules.ingestion.application.commands.update_document_meta import UpdateDocumentMeta, UpdateDocumentMetaHandler
from app.modules.ingestion.application.commands.upload_document import UploadDocument, UploadDocumentHandler
from app.modules.ingestion.application.image_store import document_store
from app.modules.ingestion.application.queries.check_duplicates import CheckDuplicates, CheckDuplicatesHandler
from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.application.stages.ai_split import AiSplitter
from app.modules.ingestion.application.stages.difficulty_suggest import DifficultySuggester
from app.modules.ingestion.application.stages.extract import Extractor
from app.modules.ingestion.application.stages.topic_suggest import Stored, TopicSuggester
from app.modules.ingestion.domain.entities import AiModel, SourceDocument
from app.modules.ingestion.domain.errors import DocxError, LlmError
from app.modules.ingestion.domain.ports import ChatResult, TopicNode
from app.modules.ingestion.domain.services.documents import UnsupportedFile
from app.modules.ingestion.domain.services.lines import Line
from app.modules.ingestion.domain.services.splitter import ParsedQuestion
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeAudit, FakeUow

ORG = uuid.uuid4()
SUBJECT = uuid.uuid4()
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
ADMIN = Actor(user_id=uuid.uuid4(), org_id=ORG, role="org_admin")
DOCX = b"PK\x03\x04" + b"word" * 10
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (4).to_bytes(4, "big") + (3).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"


class FakeDocuments:
    def __init__(self, *docs):
        self.rows = {d.id: d for d in docs}
        self.removed = []

    def get(self, org_id, document_id):
        d = self.rows.get(document_id)
        return d if d is not None and d.organization_id == org_id else None

    def get_any(self, document_id):
        return self.rows.get(document_id)

    def by_hash(self, org_id, file_hash):
        return next((d for d in self.rows.values() if d.organization_id == org_id and d.file_hash == file_hash), None)

    def of_org(self, org_id):
        return [d for d in self.rows.values() if d.organization_id == org_id]

    def add(self, doc):
        self.rows[doc.id] = doc

    def remove(self, doc):
        self.removed.append(doc.id)
        del self.rows[doc.id]


class FakeFiles:
    def __init__(self, **objects):
        self.objects = dict(objects)
        self.deleted = []

    def put(self, key, data, content_type):
        self.objects[key] = data

    def get(self, key):
        return self.objects[key], "application/octet-stream"

    def delete(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)


class FakeJobs:
    def __init__(self):
        self.queued = []

    def enqueue(self, kind, payload, max_attempts=3):
        self.queued.append((kind, payload))
        return uuid.uuid4()


class FakeSettings:
    def __init__(self, stored=None):
        self.stored = stored or {}

    def ingestion(self, org_id):
        return self.stored

    def save_ingestion(self, org_id, values):
        self.stored = values


class FakeTaxonomy:
    def __init__(self):
        self.tags = {}

    def subjects(self, org_id):
        return [(SUBJECT, "Toán", "toan")]

    def subject_in_org(self, org_id, subject_id):
        return subject_id == SUBJECT

    def semester_codes(self, org_id):
        return {"hk1", "hk2"}

    def subject_id_by_code(self, org_id, code):
        return SUBJECT if code == "toan" else None

    def topics(self, org_id, subject_id):
        return [TopicNode(uuid.uuid4(), "Mệnh đề", "toan.l10.menh_de", None)]

    def topic(self, topic_id):
        return None

    def source_tag(self, org_id, name):
        return self.tags.setdefault(name.lower(), uuid.uuid4()) if name else None


class FakeBank:
    def __init__(self):
        self.removed, self.added, self.topics, self.followed = [], [], [], []
        self.difficulties: dict = {}   # question id -> (level, source), as the pipeline's difficulty pass writes it
        self.manual: set = set()       # questions a teacher graded: the bank refuses to move those (ADR-04)
        self.kept: set = set()
        self.near: dict = {}  # question id -> [(topic id, similarity)] for the tagging queue's kNN

    def remove_document_questions(self, document_id, keep_statuses, keep_used):
        self.removed.append((document_id, keep_statuses, keep_used))

    def kept_positions(self, document_id):
        return set(self.kept)

    def add_parsed(self, org_id, document_id, drafts, tag_id):
        ids = [uuid.uuid4() for _ in drafts]
        self.added += [(d, tag_id) for d in drafts]
        return ids

    def triage(self, question_ids, threshold, seed):
        return {"auto_approved": len(question_ids), "needs_review": 0, "duplicate": 0, "spot_check": 0}

    def nearest_topic(self, question_id):
        return None

    def nearest_topics(self, org_id, subject_id, question_id, limit):
        return self.near.get(question_id, [])[:limit]

    def suggest_topic(self, question_id, topic_id, source, score):
        self.topics.append((question_id, topic_id, source))

    def set_difficulty(self, levels):
        written: dict = {}
        for qid, (level, source) in levels.items():
            if qid in self.manual:
                continue
            self.difficulties[qid] = (level, source)
            written[source] = written.get(source, 0) + 1
        return written

    def follow_document(self, document_id, changes, old_tag_id, new_tag_id):
        self.followed.append((document_id, changes, old_tag_id, new_tag_id))

    def flush(self):
        pass


class FakeModels:
    def __init__(self, *models):
        self.rows = {m.id: m for m in models}

    def get(self, model_id):
        return self.rows.get(model_id)

    def add(self, m):
        self.rows[m.id] = m

    def remove(self, m):
        del self.rows[m.id]


class FakeCipher:
    def encrypt(self, plain):
        return "enc:" + plain[::-1]

    def decrypt(self, token):
        return token[4:][::-1] if token else None


def _doc(**kw) -> SourceDocument:
    base = dict(organization_id=ORG, filename="de.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                size=10, file_hash="h" * 64, storage_key=f"{ORG}/documents/x/de.docx", status="parsed")
    return SourceDocument(**{**base, **kw})


def _upload(docs=None, files=None, settings=None):
    docs, files, jobs, audit, uow, taxonomy = docs or FakeDocuments(), files or FakeFiles(), FakeJobs(), FakeAudit(), FakeUow(), FakeTaxonomy()
    settings = settings or FakeSettings()
    reparse = ReparseDocumentHandler(docs, settings, jobs, audit, uow)
    meta = UpdateDocumentMetaHandler(docs, taxonomy, FakeBank(), audit, uow)
    return UploadDocumentHandler(docs, files, settings, taxonomy, jobs, audit, reparse, meta, uow), docs, files, jobs, audit, uow


# ------------------------------------------------------------------ upload


def test_upload_stores_queues_and_audits():
    handle, docs, files, jobs, audit, uow = _upload(settings=FakeSettings({"split_mode": "rule_ai", "threshold": 0.9}))
    doc, action = handle(TEACHER, UploadDocument("Đề thi.docx", DOCX, {"subject_id": str(SUBJECT), "grade": "11"}, {"ocr": "vision"}))
    assert action == "created" and doc.status == "queued" and doc.uploaded_by == TEACHER.user_id
    assert doc.file_hash == hashlib.sha256(DOCX).hexdigest() and files.objects[doc.storage_key] == DOCX
    assert doc.storage_key == f"{ORG}/documents/{doc.id}/_thi.docx" and doc.filename == "Đề thi.docx"
    assert doc.meta == {"subject_id": str(SUBJECT), "grade": 11}
    assert doc.processing_config["split_mode"] == "rule_ai" and doc.processing_config["threshold"] == 0.9 and doc.processing_config["ocr"] == "vision"
    assert jobs.queued == [("ingest_document", {"document_id": str(doc.id)})]
    assert audit.actions() == ["document.upload"] and uow.commits == 1


def test_same_content_is_skipped_or_reparsed_never_stored_twice():
    existing = _doc(file_hash=hashlib.sha256(DOCX).hexdigest(), meta={"grade": 10, "detected": {"grade": 12}})
    handle, docs, files, jobs, audit, _ = _upload(docs=FakeDocuments(existing))
    doc, action = handle(TEACHER, UploadDocument("copy.docx", DOCX, {}, {}))
    assert (doc, action) == (existing, "skipped") and not files.objects and not jobs.queued
    doc, action = handle(TEACHER, UploadDocument("copy.docx", DOCX, {"exam_kind": "Thi thử"}, {}, on_duplicate="replace"))
    assert (doc, action) == (existing, "reparsed") and doc.status == "queued"
    assert doc.meta == {"grade": 10, "exam_kind": "Thi thử", "detected": {"grade": 12}}  # merged, detection kept
    assert audit.actions() == ["document.reparse", "document.meta"] and len(jobs.queued) == 1


def test_replace_a_same_name_document_swaps_its_file():
    target = _doc()
    old_key = target.storage_key
    handle, docs, files, jobs, audit, _ = _upload(docs=FakeDocuments(target), files=FakeFiles(**{old_key: b"old"}))
    doc, action = handle(TEACHER, UploadDocument("de.docx", DOCX, {}, {}, on_duplicate="replace", replace_id=target.id))
    assert action == "replaced" and doc is target and doc.status == "queued" and doc.storage_key != old_key
    assert files.deleted == [old_key] and audit.actions() == ["document.replace"]
    target.status = "processing"
    with pytest.raises(Conflict) as e:
        handle(TEACHER, UploadDocument("de.docx", DOCX + b"x", {}, {}, on_duplicate="replace", replace_id=target.id))
    assert e.value.code == "busy"


def test_upload_validation():
    handle, *_ = _upload()
    with pytest.raises(UnsupportedFile):
        handle(TEACHER, UploadDocument("old.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"0" * 10, {}, {}))
    with pytest.raises(Invalid) as e:
        handle(TEACHER, UploadDocument("x.docx", DOCX, {"grade": 13}, {}))
    assert "grade" in e.value.fields
    with pytest.raises(Invalid) as e:
        handle(TEACHER, UploadDocument("x.docx", DOCX, {}, {}, on_duplicate="merge"))
    assert "on_duplicate" in e.value.fields


def test_duplicate_check_by_content_and_by_name():
    a = _doc(filename="Đề 1.docx", file_hash="a" * 64)
    b = _doc(filename="đề 1.docx", file_hash="b" * 64)
    out = CheckDuplicatesHandler(FakeDocuments(a, b))(TEACHER, CheckDuplicates([{"name": "ĐỀ 1.docx", "sha256": "A" * 64}]))
    assert out[0].same_file.id == a.id and [d.id for d in out[0].same_name] == [b.id]


# ------------------------------------------------------------------ re-parse, meta, delete


def test_reparse_refuses_a_busy_document_and_keeps_the_config_unless_given():
    doc = _doc(processing_config={"split_mode": "ai"})
    docs, jobs = FakeDocuments(doc), FakeJobs()
    handle = ReparseDocumentHandler(docs, FakeSettings(), jobs, FakeAudit(), FakeUow())
    handle(TEACHER, ReparseDocument(doc.id))
    assert doc.status == "queued" and doc.processing_config == {"split_mode": "ai"} and len(jobs.queued) == 1
    with pytest.raises(Conflict):
        handle(TEACHER, ReparseDocument(doc.id, {"split_mode": "rule"}))
    with pytest.raises(NotFound):
        handle(Actor(uuid.uuid4(), uuid.uuid4(), "teacher"), ReparseDocument(doc.id))


def test_meta_edit_moves_the_questions_and_the_source_tag():
    doc = _doc(meta={"source_name": "Nguồn cũ", "grade": 10, "detected": {"issuer": "x"}})
    bank, taxonomy, audit = FakeBank(), FakeTaxonomy(), FakeAudit()
    UpdateDocumentMetaHandler(FakeDocuments(doc), taxonomy, bank, audit, FakeUow())(
        TEACHER, UpdateDocumentMeta(doc.id, {"source_name": "Sở GD&ĐT Ninh Bình", "grade": 11}))
    assert doc.meta == {"source_name": "Sở GD&ĐT Ninh Bình", "grade": 11, "detected": {"issuer": "x"}}
    [(_, changes, old_tag, new_tag)] = bank.followed
    assert changes == {"grade": 11} and old_tag == taxonomy.tags["nguồn cũ"] and new_tag == taxonomy.tags["sở gd&đt ninh bình"]
    assert audit.entries[0][2] == {"changes": {"source_name": "Sở GD&ĐT Ninh Bình", "grade": 11}}


def test_delete_keeps_approved_questions_and_drops_the_file():
    doc = _doc()
    docs, files, bank = FakeDocuments(doc), FakeFiles(**{doc.storage_key: b"x"}), FakeBank()
    DeleteDocumentHandler(docs, files, bank, FakeAudit(), FakeUow())(TEACHER, DeleteDocument(doc.id))
    assert bank.removed == [(doc.id, ("approved",), False)] and files.deleted == [doc.storage_key] and docs.removed == [doc.id]


# ------------------------------------------------------------------ pipeline

LINES = ["SỞ GD&ĐT HÀ NỘI", "TRƯỜNG THPT CHU VĂN AN", "ĐỀ KIỂM TRA GIỮA KỲ I", "MÔN: TOÁN 10",
         "Câu 1. Mệnh đề nào sau đây đúng?", "A. 1", "B. 2", "C. 3", "D. 4", "Đáp án: B",
         "Câu 2. Phủ định của mệnh đề là", "A. a", "B. b", "C. c", "D. d", "Đáp án: C"]


class FakeDocx:
    def __init__(self, lines=None, error=None):
        self.lines, self.error = lines, error

    def read(self, data, store, stats=None):
        if self.error:
            raise DocxError(self.error)
        stats.update(equations=0, equations_failed=0)
        return [Line(t) for t in self.lines], []


class NoChat:
    def chat(self, *a, **kw):
        raise AssertionError("no model is configured")

    def discover(self, base_url):
        return []


def _pipeline(doc, docx, models=None, chat=None):
    docs, bank, taxonomy, uow = FakeDocuments(doc), FakeBank(), FakeTaxonomy(), FakeUow()
    models, chat = models or FakeModels(), chat or NoChat()
    ai = AiSplitter(models, chat, scanner=None)
    handle = IngestDocumentHandler(docs, FakeFiles(**{doc.storage_key: b"file"}), lambda d, w, s: (lambda data, page=None: None),
                                   Extractor(docx, None, None, ai), ai, taxonomy, bank, TopicSuggester(taxonomy, bank, models, chat),
                                   DifficultySuggester(bank, models, chat), lambda: "now", uow)
    return handle, bank, uow, taxonomy


def test_pipeline_parses_detects_the_header_and_hands_questions_to_the_bank():
    doc = _doc(status="queued", meta={}, processing_config={"split_mode": "rule", "threshold": 0.85})
    handle, bank, uow, taxonomy = _pipeline(doc, FakeDocx(LINES))
    handle(IngestDocument(str(doc.id)))
    assert doc.status == "parsed" and doc.question_count == 2 and doc.finished_at == "now" and uow.commits == 2
    assert [s["step"] for s in doc.log] == ["download", "extract", "split", "persist", "triage", "suggest_topics", "suggest_difficulty"]
    assert doc.meta["subject_id"] == str(SUBJECT) and doc.meta["grade"] == 10 and doc.meta["exam_kind"] == "Giữa kỳ"
    assert bank.removed == [(doc.id, ("approved",), True)]
    drafts = [d for d, _ in bank.added]
    assert [(d["number"], d["answer"], d["status"], d["source"]) for d in drafts] == [(1, {"key": "B"}, "draft", "document"), (2, {"key": "C"}, "draft", "document")]
    assert drafts[0]["subject_id"] == SUBJECT and drafts[0]["grade"] == 10
    assert doc.meta["source_name"] == "Trường THPT Chu Văn An"  # the detected issuer is the source and tags the questions
    assert {tag for _, tag in bank.added} == {taxonomy.tags["trường thpt chu văn an"]}
    assert [src for _, _, src in bank.topics] == ["auto", "auto"]  # "Mệnh đề" is a keyword cue


def test_pipeline_keeps_approved_positions():
    doc = _doc(status="queued", meta={})
    handle, bank, _, _ = _pipeline(doc, FakeDocx(LINES))
    bank.kept = {(None, 1)}
    handle(IngestDocument(str(doc.id)))
    assert [d["number"] for d, _ in bank.added] == [2] and doc.question_count == 2  # 1 new + 1 kept


def _difficulty_doc(**config):
    return _doc(status="queued", meta={}, processing_config={"split_mode": "rule", "threshold": 0.85, **config})


def test_every_parsed_question_ends_with_a_level_without_any_model():
    """AC-01: the position rule alone covers the whole paper, so the coverage does not depend on a model at all."""
    doc = _difficulty_doc()
    handle, bank, _, _ = _pipeline(doc, FakeDocx(LINES))
    handle(IngestDocument(str(doc.id)))
    assert len(bank.difficulties) == len(bank.added) == 2
    assert set(bank.difficulties.values()) == {("nb", "auto")}  # câu 1 and 2 of a paper with no PHẦN header
    assert doc.log[-1]["step"] == "suggest_difficulty" and doc.log[-1] == {"step": "suggest_difficulty", "ms": doc.log[-1]["ms"],
                                                                          "rule": 2, "ai": 0}


def test_the_model_leads_where_it_answers_and_the_rule_fills_the_rest():
    """AC-02: the model is the only signal that reads the question, so its answer wins — and the questions it
    skipped are not left empty."""
    tag = AiModel(name="Qwen", provider="ollama", model="q7", organization_id=ORG)
    chat = FakeChat(json.dumps({"results": [{"number": 1, "level": "vdc"}]}))
    doc = _difficulty_doc(tag_model=str(tag.id))
    handle, bank, _, _ = _pipeline(doc, FakeDocx(LINES), models=FakeModels(tag), chat=chat)
    handle(IngestDocument(str(doc.id)))
    assert sorted(bank.difficulties.values()) == [("nb", "auto"), ("vdc", "ai")]
    assert "Trả về đúng 2 phần tử, cho các câu: 1, 2." in chat.calls[-1]["user"]
    assert doc.log[-1]["rule"] == 1 and doc.log[-1]["ai"] == 1


@pytest.mark.parametrize("failure", [LlmError("Model không trả về JSON"), LlmError("Model không phản hồi kịp (timeout)")])
def test_a_broken_model_is_a_warning_and_the_paper_is_still_parsed(failure):
    """AC-03: missing, disabled, slow or rambling, the model never costs the teacher the upload — the levels come
    from the rule and the document's log says what happened."""
    tag = AiModel(name="Qwen", provider="ollama", model="q7", organization_id=ORG)
    doc = _difficulty_doc(tag_model=str(tag.id))
    handle, bank, _, _ = _pipeline(doc, FakeDocx(LINES), models=FakeModels(tag), chat=FakeChat(failure))
    handle(IngestDocument(str(doc.id)))
    assert doc.status == "parsed" and set(bank.difficulties.values()) == {("nb", "auto")}
    assert any("Model đoán mức độ lỗi" in w for w in doc.log[-1]["items"])


def test_a_disabled_or_foreign_model_is_simply_not_asked():
    off = AiModel(name="Qwen", provider="ollama", model="q7", organization_id=ORG, enabled=False)
    doc = _difficulty_doc(tag_model=str(off.id))
    handle, bank, _, _ = _pipeline(doc, FakeDocx(LINES), models=FakeModels(off), chat=NoChat())
    handle(IngestDocument(str(doc.id)))
    assert set(bank.difficulties.values()) == {("nb", "auto")} and not doc.log[-1].get("items")


def test_a_level_a_teacher_set_is_left_where_it_is_and_each_part_gets_its_own_band():
    """ADR-04: the bank refuses to move a `manual` level, so a re-parse cannot undo a teacher's correction. The
    stage reads the paper's parts as the rule defines them: Phần I câu 1 is the mildest, Phần III câu 5 the hardest."""
    doc, bank = _difficulty_doc(), FakeBank()
    graded, fresh = uuid.uuid4(), uuid.uuid4()
    bank.manual.add(graded)
    rows = [(ParsedQuestion(number=1, part="1", type="mcq", stem="a"), Stored(graded, "a", [])),
            (ParsedQuestion(number=5, part="3", type="short_answer", stem="b"), Stored(fresh, "b", []))]
    run = IngestRun(doc)
    DifficultySuggester(bank, FakeModels(), NoChat())(doc, rows, run)
    assert bank.difficulties == {fresh: ("vdc", "auto")}
    assert run.log[-1]["rule"] == 1 and run.log[-1]["ai"] == 0


def test_pipeline_failure_fit_for_the_teacher_is_recorded():
    doc = _doc(status="queued")
    handle, bank, uow, _ = _pipeline(doc, FakeDocx(error="Không đọc được file Word: hỏng"))
    handle(IngestDocument(str(doc.id)))
    assert doc.status == "failed" and doc.error == "Không đọc được file Word: hỏng" and uow.rollbacks == 1
    assert [s["step"] for s in doc.log] == ["download", "failed"] and not bank.added


def test_crash_after_the_last_retry_hides_the_traceback():
    doc = _doc(status="processing", log=[{"step": "download"}])
    MarkIngestFailedHandler(FakeDocuments(doc), lambda: "now", FakeUow())(MarkIngestFailed(str(doc.id), "KeyError: 'x'\nTraceback …"))
    assert doc.status == "failed" and "Traceback" not in doc.error and doc.log[-1] == {"step": "crashed", "error": "KeyError: 'x'"}


def test_document_store_converts_metafiles_and_skips_bad_pictures():
    class Vector:
        def kind(self, data):
            return "wmf" if data.startswith(b"WMF") else None

        def to_png(self, data):
            return PNG if data == b"WMF-figure" else (b"" if data == b"WMF-blank" else None)

    class Assets:
        def __init__(self):
            self.rows = []

        def add(self, a):
            self.rows.append(a)

    assets, doc_id, warnings, stats = Assets(), uuid.uuid4(), [], {}
    store = document_store(StoreImage(assets, FakeFiles()), Vector(), ORG, doc_id, warnings, stats)
    assert store(b"WMF-figure", 2) == str(assets.rows[0].id) and assets.rows[0].source_document_id == doc_id and assets.rows[0].page == 2
    assert store(b"WMF-blank") is None and store(b"WMF-broken") is None
    assert stats == {"vector_images": 1, "vector_failed": 1} and warnings == ["Bỏ qua một hình không hỗ trợ (EMF/WMF/SVG hoặc quá lớn)"]


# ------------------------------------------------------------------ AI models and settings


def test_ai_model_key_is_encrypted_and_only_managers_edit():
    models, audit = FakeModels(), FakeAudit()
    view = CreateAiModelHandler(models, FakeCipher(), audit, FakeUow())(
        ADMIN, CreateAiModel(name="GPT", provider="openai", model="gpt-4o-mini", api_key="sk-secret", is_free=False))
    stored = models.get(view.id)
    assert view.has_key and view.editable and not view.system and view.base_url == "https://api.openai.com/v1"
    assert stored.api_key_enc == "enc:terces-ks" and stored.organization_id == ORG
    with pytest.raises(Forbidden):
        CreateAiModelHandler(models, FakeCipher(), audit, FakeUow())(TEACHER, CreateAiModel(name="x", provider="ollama", model="q"))
    with pytest.raises(Forbidden):
        UpdateAiModelHandler(models, FakeCipher(), audit, FakeUow())(TEACHER, UpdateAiModel(view.id, {"name": "y"}))
    cleared = UpdateAiModelHandler(models, FakeCipher(), audit, FakeUow())(ADMIN, UpdateAiModel(view.id, {"api_key": "", "name": " GPT mini "}))
    assert not cleared.has_key and cleared.name == "GPT mini"
    with pytest.raises(Invalid):
        UpdateAiModelHandler(models, FakeCipher(), audit, FakeUow())(ADMIN, UpdateAiModel(view.id, {"provider": "bogus"}))
    assert audit.actions() == ["ai_model.create", "ai_model.update"]


def test_processing_defaults_need_usable_models():
    text_only = AiModel(name="q", provider="ollama", model="q", organization_id=ORG, capabilities=["text"])
    foreign = AiModel(name="f", provider="ollama", model="f", organization_id=uuid.uuid4())
    settings = FakeSettings()
    handle = SaveIngestionSettingsHandler(settings, FakeModels(text_only, foreign), FakeAudit(), FakeUow())
    with pytest.raises(Forbidden):
        handle(TEACHER, SaveIngestionSettings({"split_mode": "rule"}))
    with pytest.raises(Invalid):
        handle(ADMIN, SaveIngestionSettings({"split_models": [str(foreign.id)]}))
    with pytest.raises(Invalid) as e:
        handle(ADMIN, SaveIngestionSettings({"vision_model": str(text_only.id)}))
    assert "vision_model" in e.value.fields
    cfg = handle(ADMIN, SaveIngestionSettings({"split_mode": "rule_ai", "split_models": [str(text_only.id)], "threshold": 7, "ocr": "x"}))
    assert cfg["threshold"] == 1.0 and cfg["ocr"] == "auto" and settings.stored == cfg


# ------------------------------------------------------------------ the tagging queue's model pass (ADR-04)

TAG_TREE = [("Mệnh đề", "menh_de"), ("Xác suất cổ điển", "xac_suat"), ("Đạo hàm", "dao_ham"), ("Tích phân", "tich_phan")]


class QueueTaxonomy:
    """All the tagging queue asks of the taxonomy: the topics of one subject."""

    def __init__(self):
        self.rows = [TopicNode(uuid.uuid4(), name, f"toan.{code}", None) for name, code in TAG_TREE]

    def topics(self, org_id, subject_id):
        return self.rows


class FakeChat:
    """The tagging model: one scripted reply per call (an Exception is raised instead), and what it was asked."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def chat(self, m, system, user, images=None, json_mode=True, timeout=None, schema=None):
        self.calls.append({"model": m, "user": user, "timeout": timeout})
        reply = self.replies.pop(0) if self.replies else '{"results": []}'
        if isinstance(reply, Exception):
            raise reply
        return ChatResult(text=reply, latency_ms=1, model=m.model)

    def discover(self, base_url):
        return []


def _reply(*picked) -> str:
    """The shape a tagging model answers in: (question number, index in the listing, name, confidence)."""
    return json.dumps({"results": [{"number": n, "index": i, "name": name, "confidence": c} for n, i, name, c in picked]})


def _queue(chat=None, *, stored=None, model=None, near=None):
    """The ingestion API as the bank's tagging queue gets it, with the org's tagging model configured."""
    tag = model if model is not None else AiModel(name="Qwen", provider="ollama", model="q7", organization_id=ORG)
    taxonomy, bank = QueueTaxonomy(), FakeBank()
    bank.near = near or {}
    stored = {"tag_model": str(tag.id)} if stored is None else stored
    api = IngestionApi(taxonomy, bank, FakeSettings(stored), FakeModels(tag), chat or FakeChat())
    return api, taxonomy, bank


STRONG = "Phủ định của mệnh đề nào sau đây là mệnh đề đúng?"  # two keyword cues: a strong candidate
BLANK = "Cho hình vẽ bên, tính giá trị được hỏi"              # no cue, no neighbour


def test_the_model_is_asked_only_about_what_the_rules_could_not_place():
    chat = FakeChat(_reply((1, 2, "Đạo hàm", 0.8)))
    api, taxonomy, _ = _queue(chat)
    strong, blank = uuid.uuid4(), uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(strong, STRONG), (blank, BLANK)])
    assert got.model_used and len(chat.calls) == 1
    asked = chat.calls[0]["user"]
    assert BLANK in asked and STRONG not in asked  # the placed question never costs a token
    assert [(c.source, c.score) for c in got.by_question[strong]] == [("keyword", 0.81)]
    assert [(c.topic_id, c.source, c.score) for c in got.by_question[blank]] == [(taxonomy.rows[2].id, "ai", 0.8)]


def test_a_model_candidate_must_resolve_to_a_topic_of_the_subject():
    """A 7B model miscounts a long listing and invents names: only what resolves to a node of the tree is kept."""
    chat = FakeChat(_reply((1, 99, "Chuyên đề không có thật", 0.9), (2, 1, "Xác suất cổ điển", 0.6)))
    api, taxonomy, _ = _queue(chat)
    invented, real = uuid.uuid4(), uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(invented, BLANK), (real, BLANK)])
    assert got.by_question[invented] == []
    assert [(c.topic_id, c.source) for c in got.by_question[real]] == [(taxonomy.rows[1].id, "ai")]


def test_a_strong_keyword_candidate_is_never_outranked_by_the_model():
    chat = FakeChat(_reply((1, 1, "Xác suất cổ điển", 0.95)))
    api, taxonomy, _ = _queue(chat)
    strong = uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(strong, STRONG)])
    assert not got.model_used and chat.calls == []
    assert [(c.topic_id, c.source) for c in got.by_question[strong]] == [(taxonomy.rows[0].id, "keyword")]


def test_a_weak_candidate_is_kept_beside_the_model_and_three_is_still_the_cap():
    """The rules found neighbours but nothing convincing: the model adds to the list, it does not replace it, and
    it keeps the last slot rather than being cut off by the three-candidate cap."""
    chat = FakeChat(_reply((1, 2, "Đạo hàm", 0.9)))
    api, taxonomy, bank = _queue(chat)
    weak = uuid.uuid4()
    others = [taxonomy.rows[0], taxonomy.rows[1], taxonomy.rows[3]]  # the model picks the one they do not cover
    bank.near = {weak: [(t.id, s) for t, s in zip(others, (0.5, 0.42, 0.36))]}
    got = api.suggest_for(ORG, SUBJECT, [(weak, BLANK)]).by_question[weak]
    assert [(c.source, c.score) for c in got] == [("similar", 0.5), ("similar", 0.42), ("ai", 0.9)]


def test_the_model_sees_ten_questions_at_a_time():
    chat = FakeChat(*[_reply() for _ in range(3)])
    api, _, _ = _queue(chat)
    items = [(uuid.uuid4(), BLANK) for _ in range(23)]
    api.suggest_for(ORG, SUBJECT, items)
    assert [call["user"].count("Câu ") for call in chat.calls] == [10, 10, 3]


def test_a_failing_model_degrades_to_the_rules():
    chat = FakeChat(LlmError("Không kết nối được model: ConnectError"))
    api, taxonomy, _ = _queue(chat)
    strong, blank = uuid.uuid4(), uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(strong, STRONG), (blank, BLANK)])
    assert not got.model_used and got.by_question[blank] == []
    assert [c.topic_id for c in got.by_question[strong]] == [taxonomy.rows[0].id]


def test_a_slow_model_is_bounded_and_degrades_to_the_rules():
    chat = FakeChat(LlmError("Model không phản hồi kịp (timeout)"))
    api, _, _ = _queue(chat)
    blank = uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(blank, BLANK)])
    assert chat.calls[0]["timeout"] == MODEL_TIMEOUT_SECONDS  # the queue never waits as long as a job may
    assert not got.model_used and got.by_question[blank] == []


def test_a_garbage_answer_degrades_to_the_rules():
    api, _, _ = _queue(FakeChat("Chào bạn, tôi nghĩ câu này thuộc về đại số."))
    blank = uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(blank, BLANK)])
    assert not got.model_used and got.by_question[blank] == []


def test_one_bad_batch_does_not_lose_the_others():
    chat = FakeChat(LlmError("HTTP 500: overloaded"), _reply((11, 2, "Đạo hàm", 0.8)))
    api, taxonomy, _ = _queue(chat)
    items = [(uuid.uuid4(), BLANK) for _ in range(11)]
    got = api.suggest_for(ORG, SUBJECT, items)
    assert got.model_used and len(chat.calls) == 2
    assert [c.topic_id for c in got.by_question[items[10][0]]] == [taxonomy.rows[2].id]
    assert all(got.by_question[qid] == [] for qid, _ in items[:10])


@pytest.mark.parametrize("stored, model", [
    ({}, None),                                                                                      # none configured
    (None, AiModel(name="off", provider="ollama", model="q7", organization_id=ORG, enabled=False)),  # disabled
    (None, AiModel(name="foreign", provider="ollama", model="q7", organization_id=uuid.uuid4())),    # another org's
    ({"tag_model": "not-a-uuid"}, None),                                                             # unusable id
])
def test_a_model_that_is_absent_disabled_or_foreign_is_simply_not_used(stored, model):
    chat = FakeChat(_reply((1, 2, "Đạo hàm", 0.9)))
    api, _, _ = _queue(chat, stored=stored, model=model)
    blank = uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(blank, BLANK)])
    assert not got.model_used and chat.calls == [] and got.by_question[blank] == []


def test_the_caller_can_ask_the_rules_alone():
    chat = FakeChat(_reply((1, 2, "Đạo hàm", 0.9)))
    api, _, _ = _queue(chat)
    blank = uuid.uuid4()
    got = api.suggest_for(ORG, SUBJECT, [(blank, BLANK)], use_model=False)
    assert not got.model_used and chat.calls == [] and got.by_question[blank] == []
