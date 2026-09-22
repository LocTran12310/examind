from sqlalchemy import select

from app.modules.bank.domain.entities import Question

from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.bank.domain.services.search_text import for_question
from app.modules.bank.interface.deps import bank_api
from tests.factories import make_org
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload


def statuses(db, doc_id):
    out = {}
    for q in db.scalars(select(Question).where(Question.source_document_id == doc_id)):
        out[q.status] = out.get(q.status, 0) + 1
    return out


def test_golden_docx_mostly_auto_approved(client, db):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "de.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    s = statuses(db, doc_id)
    assert s.get("needs_review", 0) / 40 <= 0.15, s
    spot = db.scalars(select(Question).where(Question.source_document_id == doc_id, Question.spot_check.is_(True))).all()
    assert len(spot) == 2 and all(q.status == "auto_approved" for q in spot)
    log = client.get(f"/api/documents/{doc_id}").json()["log"]
    assert any(l["step"] == "triage" for l in log)


def test_messy_doc_goes_to_review(client, db):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    s = statuses(db, doc_id)
    assert s.get("needs_review") == 5 and s.get("auto_approved") == 3


def test_pdf_copy_of_docx_is_marked_duplicate(client, db):
    teacher_with_taxonomy(client, db)
    upload(client, "de.docx", sample("de-mau-toan10.docx"))
    run_jobs()
    pdf_id = upload(client, "de.pdf", sample("de-mau-toan10.pdf")).json()["document"]["id"]
    run_jobs()
    db.expire_all()
    rows = db.scalars(select(Question).where(Question.source_document_id == pdf_id)).all()
    dups = [q for q in rows if q.status == "duplicate"]
    assert len(dups) >= 36, statuses(db, pdf_id)
    original = db.get(Question, dups[0].duplicate_of)
    assert original.number == dups[0].number and original.source_document_id != pdf_id


def test_legacy_drafts_triaged(db):
    org = make_org(db)
    q = Question(organization_id=org.id, type="mcq", stem="Đề", options=[{"label": l, "content": l} for l in "ABCD"], answer={"key": "A"},
                 solution="g", status="draft", issues=[], confidence=1.0)
    db.add(q)
    db.commit()
    assert bank_api(db).triage_legacy_drafts() == 1
    assert q.status == "auto_approved" and q.search_text


def test_same_template_different_numbers_is_not_duplicate(db):
    org = make_org(db)
    opts = [{"label": l, "content": l} for l in "ABCD"]
    a = Question(organization_id=org.id, type="mcq", stem="Tọa độ đỉnh của parabol $y = x^2 - 4x + 3$ là", options=opts,
                 answer={"key": "A"}, solution="g", issues=[], confidence=1.0, status="approved", search_text="")
    db.add(a)
    db.flush()
    a.search_text = for_question(a.stem, a.options)
    b = Question(organization_id=org.id, type="mcq", stem="Tọa độ đỉnh của parabol $y = x^2 - 6x + 5$ là", options=opts,
                 answer={"key": "A"}, solution="g", issues=[], confidence=1.0, status="draft")
    c = Question(organization_id=org.id, type="mcq", stem="Tọa độ đỉnh của parabol y = x² - 4x + 3 là", options=opts,
                 answer={"key": "A"}, solution="g", issues=[], confidence=1.0, status="draft")
    db.add_all([b, c])
    db.flush()
    bank_api(db).triage([b, c], 0.85)
    assert b.status == "auto_approved" and c.status == "duplicate" and c.duplicate_of == a.id
