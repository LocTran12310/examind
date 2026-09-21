import subprocess

from sqlalchemy import select

from app.models import Question, Topic
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin


def docx(md: str) -> bytes:
    out = subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", "-o", "-"], input=md.encode(), capture_output=True, check=True)
    return out.stdout


def test_knn_from_approved_question(client, db):
    setup_admin(client, db)
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    q2 = db.scalar(select(Question).where(Question.source_document_id == doc, Question.number == 2))
    topic = db.scalar(select(Topic).where(Topic.name == "Lũy thừa với số mũ thực"))
    opts = [{"label": l, "content": c} for l, c in zip("ABCD", ["3", "4", "5", "8"])]
    client.patch(f"/api/questions/{q2.id}", json={"type": "mcq", "options": opts, "answer": {"key": "B"}, "primary_topic_id": str(topic.id)})
    assert client.post(f"/api/review/questions/{q2.id}/action", json={"action": "approve"}).status_code == 200
    new = docx("Câu 1. Giá trị của $2^{2}$ bằng bao nhiêu? Các lựa chọn: 3; 4; 5; 9.\n\nA. 3\n\nB. 4\n\nC. 5\n\nD. 9\n\nĐáp án: B\n")
    doc2 = upload(client, "new.docx", new).json()["document"]["id"]
    run_jobs()
    got = client.get(f"/api/documents/{doc2}/questions").json()[0]["topics"][0]
    assert got["name"] == "Lũy thừa với số mũ thực" and got["source"] == "knn" and got["score"] >= 0.35


def test_strong_keyword_wins_over_knn(client, db):
    setup_admin(client, db)
    doc = upload(client, "m.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    qs = client.get(f"/api/documents/{doc}/questions").json()
    assert all(q["topics"][0]["source"] == "auto" for q in qs if q["topics"])
