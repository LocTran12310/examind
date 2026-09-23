from sqlalchemy import select

from app.modules.bank.domain.entities import Question, ReviewEvent
from app.modules.identity.domain.entities import Organization
from app.modules.taxonomy.domain.topics import Topic
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin


def kho(client, db):
    setup_admin(client, db)
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    return doc


def mau(client, db):
    """The paper the classifier handles well: auto-approved questions, and a spot check among them."""
    setup_admin(client, db)
    doc = upload(client, "m.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    return doc


def test_queue_groups_and_spot_checks_last(client, db):
    doc = kho(client, db)
    q = client.get(f"/api/review/documents/{doc}/queue").json()
    assert len(q) == 8  # 5 fail the parse rules, the other 3 carry no cue (topic-coverage ADR-02)
    assert q[0]["group"] == "không nhận ra phương án" and not any(x["spot_check"] for x in q)
    doc = upload(client, "m.docx", sample("de-mau-toan10.docx")).json()["document"]["id"]
    run_jobs()
    q = client.get(f"/api/review/documents/{doc}/queue").json()
    assert q[-1]["group"] == "Kiểm tra ngẫu nhiên" and q[-1]["spot_check"]


def test_approve_refuses_blocking_then_answer_edit_and_approve(client, db):
    doc = kho(client, db)
    q1 = client.get(f"/api/review/documents/{doc}/queue").json()[0]
    r = client.post(f"/api/review/questions/{q1['id']}/action", json={"action": "approve"})
    assert r.status_code == 409 and r.json()["code"] == "has_blocking_issues"
    opts = [{"label": l, "content": c} for l, c in zip("ABCD", ["1", "2", "3", "4"])]
    r = client.patch(f"/api/questions/{q1['id']}", json={"type": "mcq", "options": opts, "stem": "Giá trị của $2^1$?", "answer": {"key": "B"}})
    assert r.status_code == 200, r.text
    assert r.json()["issues"] == ["thiếu lời giải"] and r.json()["confidence"] == 1.0
    r = client.post(f"/api/review/questions/{q1['id']}/action", json={"action": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    actions = [e.action for e in db.scalars(select(ReviewEvent).where(ReviewEvent.question_id == q1["id"]).order_by(ReviewEvent.created_at))]
    assert actions == ["edit", "approve"]
    assert client.patch(f"/api/questions/{q1['id']}", json={"answer": {"key": "E"}}).status_code == 422


def test_reject_restore_and_topics_tags(client, db):
    admin_doc = kho(client, db)
    q = client.get(f"/api/review/documents/{admin_doc}/queue").json()[1]
    assert client.post(f"/api/review/questions/{q['id']}/action", json={"action": "reject"}).json()["status"] == "rejected"
    assert client.post(f"/api/review/questions/{q['id']}/action", json={"action": "restore"}).json()["status"] == "needs_review"
    topic = db.scalar(select(Topic).where(Topic.name == "Lũy thừa với số mũ thực"))
    tag = client.post("/api/tags", json={"group": "method", "name": "tính nhẩm"}).json()
    r = client.patch(f"/api/questions/{q['id']}", json={"primary_topic_id": str(topic.id), "tag_ids": [tag["id"]], "difficulty": "nb"})
    body = r.json()
    assert body["topics"][0]["name"] == "Lũy thừa với số mũ thực" and body["topics"][0]["source"] == "manual"
    assert [t["name"] for t in body["tags"]] == ["tính nhẩm"] and body["difficulty"] == "nb"


def test_spot_check_failures_raise_threshold(client, db):
    admin = setup_admin(client, db)
    for name in ("de-mau-toan10.docx", "de-thpt2025-toan.docx"):
        upload(client, name, sample(name))
    run_jobs()
    spots = db.scalars(select(Question).where(Question.spot_check.is_(True), Question.status == "auto_approved")).all()
    assert len(spots) >= 2
    client.post(f"/api/review/questions/{spots[0].id}/action", json={"action": "reject"})
    org = db.get(Organization, admin.organization_id)
    db.refresh(org)
    assert (org.settings or {}).get("ingestion", {}).get("threshold", 0.85) == 0.85
    r = client.patch(f"/api/questions/{spots[1].id}", json={"solution": "Sửa lời giải"})
    assert r.json()["status"] == "approved"
    db.refresh(org)
    assert org.settings["ingestion"]["threshold"] == 0.9


def test_spot_ok_is_recorded(client, db):
    doc = mau(client, db)
    spot = client.get(f"/api/review/documents/{doc}/queue").json()[-1]
    assert client.post(f"/api/review/questions/{spot['id']}/action", json={"action": "approve"}).json()["status"] == "approved"
    assert db.scalar(select(ReviewEvent.action).where(ReviewEvent.question_id == spot["id"])) == "spot_ok"


def test_ocr_question_approved_by_teacher_clears_flag(client, db):
    setup_admin(client, db)
    doc = upload(client, "scan.pdf", sample("de-scan.pdf")).json()["document"]["id"]
    run_jobs()
    q = next(x for x in client.get(f"/api/review/documents/{doc}/queue").json() if x["group"] == "OCR" and len(x["options"]) == 4 and x["answer"])
    r = client.post(f"/api/review/questions/{q['id']}/action", json={"action": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "approved" and "OCR" not in r.json()["issues"]
