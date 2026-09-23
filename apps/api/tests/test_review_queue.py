from sqlalchemy import select

from app.modules.bank.domain.entities import Question, ReviewEvent
from app.modules.identity.domain.entities import Organization
from app.modules.taxonomy.domain.topics import Topic
from tests.factories import make_org, make_user
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


def test_document_questions_by_state(client, db):
    """Every question of a document is reachable, filtered by state (AC-03); the keyboard queue is unchanged."""
    doc = kho(client, db)
    s = lambda **b: client.post(f"/api/review/documents/{doc}/questions/search", json=b)  # noqa: E731
    body = s().json()
    assert set(body) == {"data", "total", "page", "limit"} and body["total"] == 8
    assert {q["status"] for q in body["data"]} == {"needs_review"} and all(q["group"] for q in body["data"])
    assert s(state="approved").json()["total"] == 0 and s(state="duplicate").json()["total"] == 0
    # "all" is the document page's order — the same as the questions list of the document
    assert [q["id"] for q in s(state="all", limit=100).json()["data"]] == [q["id"] for q in client.get(f"/api/documents/{doc}/questions").json()]
    page = s(state="all", limit=3, page=2).json()
    assert page["total"] == 8 and page["page"] == 2 and len(page["data"]) == 3
    assert [q["number"] for q in s(state="all", filters={"number": {"from": 1, "to": 2}}).json()["data"]] == [1, 2]
    assert s(state="all", filters={"status": {"value": "needs_review"}}).json()["total"] == 8
    for bad, code in [(dict(state="xem"), "bad_filter"), (dict(filters={"status": {"value": "nope"}}), "bad_filter"),
                      (dict(sort=[{"field": "nope"}]), "bad_sort")]:
        r = s(**bad)
        assert r.status_code == 422 and r.json()["code"] == code, bad
    other = client.__class__(client.app)
    org = make_org(db, "orgb")
    make_user(db, org, "gvb", role="teacher")
    db.commit()
    other.post("/api/auth/login", json={"org_code": "orgb", "username": "gvb", "password": "Secret123!"})
    assert other.post(f"/api/review/documents/{doc}/questions/search", json={}).status_code == 404


def test_states_partition_the_document(client, db):
    doc = mau(client, db)
    s = lambda state: client.post(f"/api/review/documents/{doc}/questions/search", json={"state": state, "limit": 200}).json()  # noqa: E731
    row = client.get(f"/api/review/documents/{doc}").json()
    per_state = {st: s(st)["total"] for st in ("pending", "approved", "rejected", "duplicate")}
    assert per_state["pending"] == row["pending"] == row["counts"]["needs_review"] + row["counts"]["flagged"] + row["spot_pending"]
    assert sum(per_state.values()) == s("all")["total"] == row["total"] == 40
    # the check sample waits with the rest, and says so
    assert [q["group"] for q in s("pending")["data"] if q["spot_check"]] == ["Kiểm tra ngẫu nhiên"] * row["spot_pending"]


def test_a_re_decision_moves_the_counts_and_the_state(client, db):
    """A decision taken back is the same command (ADR-02); the document's counts and state follow it (AC-04)."""
    doc = kho(client, db)
    row = lambda: client.get(f"/api/review/documents/{doc}").json()  # noqa: E731
    ids = lambda state: [q["id"] for q in client.post(f"/api/review/documents/{doc}/questions/search",  # noqa: E731
                                                      json={"state": state, "limit": 200}).json()["data"]]
    assert row()["review_state"] == "pending" and row()["pending"] == 8
    q = client.get(f"/api/review/documents/{doc}/queue").json()[0]
    opts = [{"label": l, "content": c} for l, c in zip("ABCD", ["1", "2", "3", "4"])]
    client.patch(f"/api/questions/{q['id']}", json={"type": "mcq", "options": opts, "stem": "Giá trị của $2^1$?", "answer": {"key": "B"}})
    assert client.post(f"/api/review/questions/{q['id']}/action", json={"action": "approve"}).json()["status"] == "approved"
    r = row()
    assert r["pending"] == 7 and r["counts"]["approved"] == 1 and r["review_state"] == "pending" and ids("approved") == [q["id"]]
    # approved → rejected
    assert client.post("/api/questions/bulk", json={"ids": [q["id"]], "set": {"status": "rejected"}}).json()["updated"] == 1
    r = row()
    assert r["counts"]["approved"] == 0 and r["counts"]["rejected"] == 1 and r["pending"] == 7 and ids("rejected") == [q["id"]]
    # rejected → back on the desk: the question is in the queue again and the count rises
    assert client.post("/api/questions/bulk", json={"ids": [q["id"]], "set": {"status": "needs_review"}}).json()["updated"] == 1
    r = row()
    assert r["pending"] == 8 and r["counts"]["needs_review"] == 8 and r["review_state"] == "pending"
    assert q["id"] in ids("pending") and len(client.get(f"/api/review/documents/{doc}/queue").json()) == 8
    assert client.post("/api/questions/bulk", json={"ids": [q["id"]], "set": {"status": "xong"}}).status_code == 422


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
