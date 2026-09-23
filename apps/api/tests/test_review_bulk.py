from sqlalchemy import select

from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.services.answer_key import parse
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin


def test_parse_formats():
    assert parse("1A 2C 3B") == {(None, 1): "A", (None, 2): "C", (None, 3): "B"}
    assert parse("1.A, 2.c; 3-B 4:D") == {(None, 1): "A", (None, 2): "C", (None, 3): "B", (None, 4): "D"}
    assert parse("A\nC\nB") == {(None, 1): "A", (None, 2): "C", (None, 3): "B"}
    assert parse("PHẦN I: 1A 2B\nPHẦN II 1C") == {("1", 1): "A", ("1", 2): "B", ("2", 1): "C"}


def test_paste_answer_key_and_approve_confident(client, db):
    setup_admin(client, db)
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    # make questions 1-5 real MCQs without answers (as after an edit)
    opts = [{"label": l, "content": c} for l, c in zip("ABCD", "1234")]
    for q in db.scalars(select(Question).where(Question.number <= 5)):
        client.patch(f"/api/questions/{q.id}", json={"type": "mcq", "options": opts})
    r = client.post(f"/api/review/documents/{doc}/answer-key", json={"text": "1B 2B 3B 4B 5B 9A"}).json()
    assert r == {"applied": 5, "approved": 5, "unmatched": [9]}
    db.expire_all()
    assert all(q.status == "approved" and q.answer == {"key": "B"} for q in db.scalars(select(Question).where(Question.number <= 5)))
    assert len(client.get(f"/api/review/documents/{doc}/queue").json()) == 3  # nothing of k.docx is auto-approved (ADR-02)
    # approve-confident takes the auto-approved questions of a paper the classifier could place, minus its spot checks
    other = upload(client, "m.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    row = client.get(f"/api/review/documents/{other}").json()
    r = client.post(f"/api/review/documents/{other}/approve-confident").json()
    assert r["approved"] == row["counts"]["auto_approved"] - row["spot_pending"] > 0
    left = client.get(f"/api/review/documents/{other}/queue").json()
    assert [q["group"] for q in left if q["spot_check"]] == ["Kiểm tra ngẫu nhiên"] * row["spot_pending"]


def test_pdf_page_image(client, db):
    setup_admin(client, db)
    doc = upload(client, "de.pdf", sample("de-mau-toan10.pdf")).json()["document"]["id"]
    run_jobs()
    r = client.get(f"/api/documents/{doc}/pages/1.png")
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert client.get(f"/api/documents/{doc}/pages/1.png").content == r.content  # cached copy
    assert client.get(f"/api/documents/{doc}/pages/99.png").status_code == 404
    q = client.get(f"/api/documents/{doc}/questions").json()
    assert q[0]["page"] == 1 and q[-1]["page"] > 1
