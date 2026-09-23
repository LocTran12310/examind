"""Finding the questions nobody placed in the topic tree and getting candidates for them
(topic-coverage AC-01, AC-02, AC-04, AC-05, AC-06, AC-07)."""
import json
import uuid

import httpx
from sqlalchemy import select

from app.modules.bank.domain.entities import Question, QuestionTopic
from app.modules.bank.domain.services.search_text import for_question
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.infrastructure.adapters import llm
from app.modules.taxonomy.domain.entities import Subject
from app.modules.taxonomy.domain.topics import Topic
from tests.factories import make_org, make_user
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload
from tests.test_review_api import setup_admin

OPTS = [{"label": l, "content": c} for l, c in zip("ABCD", "1234")]


def by_name(db, org):
    return {t.name: t for t in db.scalars(select(Topic).where(Topic.organization_id == org))}


def add_question(db, org, subject_id, stem, *, topic=None, document=None, status="auto_approved"):
    q = Question(organization_id=org, subject_id=subject_id, type="mcq", stem=stem, options=OPTS, answer={"key": "A"},
                 status=status, source_document_id=document)
    db.add(q)
    db.flush()
    q.search_text = for_question(q.stem, q.options)
    if topic is not None:
        db.add(QuestionTopic(question_id=q.id, topic_id=topic.id, is_primary=True, source="manual"))
    db.flush()
    return q


def bank(client, db):
    """An org with the seeded taxonomy, two documents and six questions — four of them without a topic."""
    admin = setup_admin(client, db)
    org = admin.organization_id
    subject = db.scalar(select(Subject).where(Subject.organization_id == org, Subject.code == "toan"))
    topics = by_name(db, org)
    docs = [SourceDocument(organization_id=org, filename=f"de{i}.docx", mime="x", size=1, file_hash=f"h{i}",
                           storage_key=f"k{i}", status="parsed") for i in (1, 2)]
    db.add_all(docs)
    db.flush()
    placed = add_question(db, org, subject.id, "Tính nguyên hàm của hàm số $f(x)$", topic=topics["Nguyên hàm"], document=docs[0].id)
    untagged = [
        add_question(db, org, subject.id, "Cho tập hợp $A$ và $B$. Tập $A \\cap B$ là", document=docs[0].id),
        add_question(db, org, subject.id, "Tính nguyên hàm của hàm số $g(x)$", document=docs[0].id),
        add_question(db, org, subject.id, "Một câu hỏi không có dấu hiệu nào cả", document=docs[1].id),
        add_question(db, org, subject.id, "Số cách chọn 3 học sinh từ 10 học sinh là", document=None),
    ]
    db.commit()
    return dict(org=org, subject=subject, topics=topics, docs=docs, placed=placed, untagged=untagged)


def suggest(client, ids, use_model=True):
    return client.post("/api/questions/suggest-topics", json={"question_ids": [str(i) for i in ids], "use_model": use_model})


def tag_model(client):
    """Register an Ollama tagging model and make it the org's default — what the queue reads (ADR-04)."""
    mid = client.post("/api/ai-models", json={"name": "tag", "provider": "ollama", "model": "tag:1", "base_url": "http://t"}).json()["id"]
    assert client.put("/api/org/settings/ingestion", json={"tag_model": mid}).status_code == 200
    return mid


def tagger(topic_name, asked, body=None):
    """A tagging model that puts every question it is shown under `topic_name`; `asked` collects the prompts."""
    def handler(request):
        user = json.loads(request.content)["messages"][-1]["content"]
        listing, questions = user.split("CÂU HỎI:")
        asked.append(questions.strip())
        if body is not None:
            return httpx.Response(200, json={"message": {"content": body}})
        idx = next(int(line.split(".")[0]) for line in listing.splitlines() if line.endswith("› " + topic_name))
        numbers = [int(x.split(":")[0].replace("Câu ", "")) for x in questions.strip().split("\n\n")]
        results = [{"number": n, "index": idx, "name": topic_name, "confidence": 0.66} for n in numbers]
        return httpx.Response(200, json={"message": {"content": json.dumps({"results": results})}})
    return httpx.MockTransport(handler)


def unreachable(exc):
    def handler(request):
        raise exc
    return httpx.MockTransport(handler)


# ------------------------------------------------------------------ T-01-01: finding them


def test_has_topic_filters_the_search(client, db):
    x = bank(client, db)
    got = client.post("/api/questions/search", json={"has_topic": False, "limit": 50}).json()
    assert got["total"] == 4 and {q["id"] for q in got["data"]} == {str(q.id) for q in x["untagged"]}
    assert all(q["topics"] == [] for q in got["data"])
    assert client.post("/api/questions/search", json={"has_topic": True}).json()["total"] == 1
    assert client.post("/api/questions/search", json={}).json()["total"] == 5
    # it composes with the other bank filters like any of them
    assert client.post("/api/questions/search", json={"has_topic": False, "document_id": str(x["docs"][0].id)}).json()["total"] == 2


def test_has_topic_keeps_the_search_contract(client, db):
    bank(client, db)
    body = {"has_topic": False, "filters": {"stem": {"operator": "*", "value": "nguyên hàm"}}, "sort": [{"field": "created_at", "desc": True}]}
    assert client.post("/api/questions/search", json=body).json()["total"] == 1
    assert client.post("/api/questions/search", json={"has_topic": False, "filters": {"nope": {"value": 1}}}).status_code == 422
    assert client.post("/api/questions/search", json={"has_topic": False, "sort": [{"field": "nope"}]}).status_code == 422
    assert client.post("/api/questions/search", json={"has_topic": "maybe"}).status_code == 422


def test_untagged_count_per_document(client, db):
    x = bank(client, db)
    f = client.post("/api/questions/facets", json={}).json()
    assert f["topics"]["none"] == 4
    assert f["untagged_documents"] == {str(x["docs"][0].id): 2, str(x["docs"][1].id): 1, "none": 1}
    # the breakdown stays whole while a teacher works one paper at a time
    f = client.post("/api/questions/facets", json={"document_id": str(x["docs"][1].id)}).json()
    assert f["topics"]["none"] == 1 and f["untagged_documents"][str(x["docs"][0].id)] == 2


# ------------------------------------------------------------------ T-01-02: suggestions on demand


def test_an_obvious_cue_comes_first(client, db):
    x = bank(client, db)
    sets, combi = x["untagged"][0], x["untagged"][3]
    got = suggest(client, [sets.id, combi.id]).json()["suggestions"]
    first = got[str(sets.id)][0]
    assert first["name"] == "Tập hợp và các phép toán" and first["source"] == "keyword" and 0 < first["score"] <= 0.95
    assert first["path"] == x["topics"]["Tập hợp và các phép toán"].path
    assert got[str(combi.id)][0]["name"] == "Hoán vị, chỉnh hợp, tổ hợp"


def test_three_candidates_at_most_best_first(client, db):
    x = bank(client, db)
    got = suggest(client, [q.id for q in x["untagged"]]).json()["suggestions"]
    assert set(got) == {str(q.id) for q in x["untagged"]}
    for candidates in got.values():
        assert len(candidates) <= 3
        assert [c["score"] for c in candidates] == sorted((c["score"] for c in candidates), reverse=True)
        assert all(c["source"] in ("keyword", "similar") for c in candidates)
        assert len({c["topic_id"] for c in candidates}) == len(candidates)


def test_a_similar_tagged_question_lends_its_topic(client, db):
    """No cue of its own, but the bank already holds a question that looks like it (ADR-01: kNN over the subject)."""
    x = bank(client, db)
    twin = add_question(db, x["org"], x["subject"].id, "Một câu hỏi không có dấu hiệu nào khác",
                        topic=x["topics"]["Xác suất cổ điển"], document=x["docs"][0].id)
    db.commit()
    assert twin.id
    got = suggest(client, [x["untagged"][2].id]).json()["suggestions"][str(x["untagged"][2].id)]
    assert got and got[0]["name"] == "Xác suất cổ điển" and got[0]["source"] == "similar" and got[0]["score"] >= 0.35


def test_the_batch_is_capped_and_scoped_to_the_org(client, db):
    x = bank(client, db)
    assert suggest(client, [uuid.uuid4() for _ in range(51)]).status_code == 422
    assert suggest(client, []).json()["suggestions"] == {}
    other = make_org(db, "orgb", "Trung tâm B")
    make_user(db, other, "gvb", role="teacher")
    stranger = add_question(db, other.id, None, "Câu của trung tâm khác")
    db.commit()
    assert suggest(client, [stranger.id]).status_code == 404
    assert suggest(client, [x["untagged"][0].id, stranger.id]).status_code == 404


# ------------------------------------------------------------------ T-03-01: what the rules cannot place


def test_the_model_places_what_the_rules_could_not(client, db, monkeypatch):
    """AC-06: a question with no cue and no neighbour gets candidates from the org's tagging model, inside the
    subject's own tree and marked `ai`; the questions the rules placed never reach the model (A-07)."""
    asked: list = []
    monkeypatch.setattr(llm, "TRANSPORT", tagger("Xác suất cổ điển", asked))
    x = bank(client, db)
    tag_model(client)
    got = suggest(client, [q.id for q in x["untagged"]]).json()
    assert got["model_used"]
    blank = got["suggestions"][str(x["untagged"][2].id)]
    assert [(c["name"], c["source"], c["score"]) for c in blank] == [("Xác suất cổ điển", "ai", 0.66)]
    assert blank[0]["path"] == x["topics"]["Xác suất cổ điển"].path
    sets = got["suggestions"][str(x["untagged"][0].id)]
    assert sets[0]["source"] == "keyword" and all(c["source"] != "ai" for c in sets)
    prompts = " ".join(asked)
    assert "không có dấu hiệu" in prompts and "\\cap" not in prompts  # only the unplaced question was sent


def test_a_model_problem_never_blocks_the_queue(client, db, monkeypatch):
    """AC-07: erroring, rambling or too slow, the answer still carries what the rules found and says model_used false."""
    x = bank(client, db)
    tag_model(client)
    ids = [q.id for q in x["untagged"]]
    rules = suggest(client, ids, use_model=False).json()
    assert rules["model_used"] is False
    broken = {"lỗi": httpx.MockTransport(lambda r: httpx.Response(500, json={"error": "overloaded"})),
              "rác": tagger("Xác suất cổ điển", [], body="Xin chào, tôi nghĩ câu này thuộc đại số."),
              "treo": unreachable(httpx.ConnectTimeout("too slow"))}
    for what, transport in broken.items():
        monkeypatch.setattr(llm, "TRANSPORT", transport)
        got = suggest(client, ids).json()
        assert got["model_used"] is False, what
        assert got["suggestions"] == rules["suggestions"], what


def test_without_a_tagging_model_the_rules_answer_alone(client, db, monkeypatch):
    """An org that configured no tagging model never waits for one (and `use_model` costs nothing)."""
    def boom(*a, **kw):
        raise AssertionError("no tagging model is configured, so none may be called")

    monkeypatch.setattr(llm.HttpChatModels, "chat", boom)
    x = bank(client, db)
    got = suggest(client, [q.id for q in x["untagged"]]).json()
    assert got["model_used"] is False and len(got["suggestions"]) == 4


# ------------------------------------------------------------------ T-01-03: the backlog stops refilling


def test_a_question_without_a_topic_waits_for_review(client, db):
    """AC-04: whatever its parse confidence, a question the classifier could not place is needs_review and the
    document log says how many there were."""
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    rows = db.scalars(select(Question).where(Question.source_document_id == doc_id)).all()
    placed = {t.question_id for t in db.scalars(select(QuestionTopic))}
    untagged = [q for q in rows if q.id not in placed]
    assert untagged and all(q.status == "needs_review" for q in untagged)
    log = client.get(f"/api/documents/{doc_id}").json()["log"]
    step = next(s for s in log if s["step"] == "suggest_topics")
    assert step["none"] == len(untagged)
    warnings = next(s["items"] for s in log if s["step"] == "warnings")
    assert f"{len(untagged)} câu chưa gắn chuyên đề" in " ".join(warnings)
    # and they are exactly what the queue lists
    assert client.post("/api/questions/search", json={"has_topic": False, "status": "all"}).json()["total"] == len(untagged)


def test_a_tagged_question_keeps_its_triage_outcome(client, db):
    """Only the unplaced ones move: everything the classifier placed keeps the status triage gave it."""
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    placed = {t.question_id for t in db.scalars(select(QuestionTopic))}
    rows = db.scalars(select(Question).where(Question.source_document_id == doc_id)).all()
    assert [q for q in rows if q.id in placed and q.status == "auto_approved"]
    assert all(q.status == "needs_review" for q in rows if q.id not in placed)


def test_a_topic_makes_the_question_leave_the_queue(client, db):
    """AC-02: the teacher's choice is written with source manual, and the count drops."""
    x = bank(client, db)
    q = x["untagged"][0]
    topic_id = suggest(client, [q.id]).json()["suggestions"][str(q.id)][0]["topic_id"]
    r = client.post("/api/questions/bulk", json={"ids": [str(q.id)], "set": {"primary_topic_id": topic_id}})
    assert r.status_code == 200 and r.json()["updated"] == 1
    assert client.post("/api/questions/search", json={"has_topic": False}).json()["total"] == 3
    link = db.scalar(select(QuestionTopic).where(QuestionTopic.question_id == q.id))
    assert str(link.topic_id) == topic_id and link.is_primary and link.source == "manual"


def test_bulk_topics_places_a_page_in_one_request(client, db):
    """pickers-builder AC-03 (ADR-02): every selected question takes its own topic in one request, source manual,
    and the pairs it cannot apply come back named."""
    x = bank(client, db)
    t, (q_set, q_int, q_plain, q_count) = x["topics"], x["untagged"]
    ly = db.scalar(select(Subject).where(Subject.organization_id == x["org"], Subject.code == "ly"))
    foreign = client.post("/api/topics", json={"name": "Dao động điều hòa", "subject_id": str(ly.id), "level_kind": "topic"})
    assert foreign.status_code == 201, foreign.text
    other_org = make_org(db, code="trungtamb", name="Trung tâm B")
    elsewhere = add_question(db, other_org.id, x["subject"].id, "Câu của đơn vị khác")
    db.commit()
    gone = str(uuid.uuid4())
    pairs = [{"question_id": str(q_set.id), "topic_id": str(t["Tập hợp và các phép toán"].id)},
             {"question_id": str(q_int.id), "topic_id": str(t["Nguyên hàm"].id)},
             {"question_id": str(q_count.id), "topic_id": str(t["Quy tắc đếm"].id)},
             {"question_id": str(q_plain.id), "topic_id": foreign.json()["id"]},
             {"question_id": str(elsewhere.id), "topic_id": str(t["Nguyên hàm"].id)},
             {"question_id": gone, "topic_id": str(t["Nguyên hàm"].id)}]
    r = client.post("/api/questions/bulk/topics", json={"pairs": pairs})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["updated"] == 3
    assert [(s["question_id"], s["reason"], s["message"]) for s in body["skipped"]] == [
        (str(q_plain.id), "subject_mismatch", "Chuyên đề không thuộc môn của câu hỏi"),
        (str(elsewhere.id), "other_org", "Câu hỏi của đơn vị khác"),
        (gone, "unknown_question", "Không tìm thấy câu hỏi")]
    link = db.scalar(select(QuestionTopic).where(QuestionTopic.question_id == q_count.id))
    assert link.topic_id == t["Quy tắc đếm"].id and link.is_primary and link.source == "manual"
    assert client.post("/api/questions/search", json={"has_topic": False}).json()["total"] == 1  # only the one left untagged
    assert client.post("/api/questions/bulk/topics", json={"pairs": pairs[:1] * 201}).status_code == 422
