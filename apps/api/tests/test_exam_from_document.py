"""'Tạo đề từ tài liệu' (official-exam-ingestion AC-11, AC-12)."""
from sqlalchemy import select, update

from app.modules.assessment.domain.entities import Exam, ExamQuestion
from app.modules.bank.domain.entities import Question
from tests.test_documents_api import run_jobs, sample, teacher_with_taxonomy, upload


def _parsed(client, db):
    teacher_with_taxonomy(client, db)
    doc = upload(client, "de-thpt2025-toan.docx", sample("de-thpt2025-toan.docx"), {"source_name": "THPT A", "exam_kind": "Thi thử", "school_year": "2024-2025"}).json()["document"]
    run_jobs()
    return doc["id"]


def test_exam_keeps_the_original_order_and_points(client, db):
    doc_id = _parsed(client, db)
    db.execute(update(Question).where(Question.source_document_id == doc_id).values(status="needs_review"))
    db.commit()
    assert client.post(f"/api/documents/{doc_id}/exam", json={}).status_code == 422  # nothing approved yet
    db.execute(update(Question).where(Question.source_document_id == doc_id).values(status="approved"))
    rejected = db.scalar(select(Question).where(Question.source_document_id == doc_id, Question.part == "1", Question.number == 5))
    rejected.status = "rejected"
    db.commit()

    r = client.post(f"/api/documents/{doc_id}/exam", json={})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["added"] == 21 and body["skipped"] == 1
    exam = db.get(Exam, body["exam_id"])
    assert exam.title == "THPT A · Thi thử · 2024-2025" and exam.source == "document"
    rows = db.execute(select(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id)
                      .where(ExamQuestion.exam_id == exam.id).order_by(ExamQuestion.position)).all()
    order = [(q.part, q.number) for _, q in rows]
    assert order == sorted(order, key=lambda k: (int(k[0]), k[1])) and ("1", 5) not in order
    assert {q.part: eq.points for eq, q in rows} == {"1": 0.25, "2": 1.0, "3": 0.5}
    assert sum(eq.points for eq, _ in rows) == 11 * 0.25 + 4 + 6 * 0.5


def test_unparsed_document_is_refused(client, db):
    teacher_with_taxonomy(client, db)
    doc = upload(client, "de-thpt2025-toan.docx", sample("de-thpt2025-toan.docx")).json()["document"]
    assert client.post(f"/api/documents/{doc['id']}/exam", json={}).status_code == 422


def test_reparse_keeps_questions_used_in_an_exam(client, db):
    doc_id = _parsed(client, db)
    db.execute(update(Question).where(Question.source_document_id == doc_id).values(status="auto_approved"))
    db.commit()
    exam_id = client.post(f"/api/documents/{doc_id}/exam", json={}).json()["exam_id"]
    assert client.post(f"/api/documents/{doc_id}/reparse", json={}).status_code == 202
    from tests.test_documents_api import run_jobs

    run_jobs()
    db.expire_all()
    d = client.get(f"/api/documents/{doc_id}").json()
    assert d["status"] == "parsed" and d["question_count"] == 22  # kept questions still count
    assert client.post(f"/api/exams/{exam_id}/questions/search", json={}).json()["total"] == 22
    assert len(client.get(f"/api/documents/{doc_id}/questions").json()) == 22  # kept, not duplicated
