from tests.factories import login_as, make_org, make_user
from tests.test_documents_api import run_jobs, sample, upload


def setup_admin(client, db):
    admin = login_as(client, db, "org_admin")
    from app.seed.org_template import seed_org

    seed_org(db, admin.organization_id)
    db.commit()
    return admin


def test_counts_progress_and_assignment(client, db):
    admin = setup_admin(client, db)
    teacher = make_user(db, admin.organization, "gv", role="teacher")
    db.commit()
    kho = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    upload(client, "m.docx", sample("de-mau-toan10.docx"))
    run_jobs()
    rows = {r["document"]["filename"]: r for r in client.post("/api/review/documents/search", json={}).json()["data"]}
    k, m = rows["k.docx"], rows["m.docx"]
    # nothing in k.docx could be classified, so all eight wait for a teacher (topic-coverage ADR-02)
    assert k["total"] == 8 and k["counts"]["needs_review"] == 8 and k["counts"]["auto_approved"] == 0
    assert k["spot_pending"] == 0 and k["progress"] == 0.0
    assert m["total"] == 40 and m["spot_pending"] == 2 and 0 < m["progress"] < 1
    r = client.patch(f"/api/review/documents/{kho}", json={"assigned_to": str(teacher.id)})
    assert r.status_code == 200 and r.json()["assigned_name"] == teacher.full_name
    t = client.__class__(client.app)
    t.post("/api/auth/login", json={"org_code": "trungtama", "username": "gv", "password": "Secret123!"})
    assert [x["document"]["filename"] for x in t.post("/api/review/documents/search", json={"mine": True}).json()["data"]] == ["k.docx"]
    assert t.patch(f"/api/review/documents/{kho}", json={"assigned_to": None}).status_code == 403
    stranger = make_user(db, make_org(db, "orgb"), "x", role="teacher")
    db.commit()
    assert client.patch(f"/api/review/documents/{kho}", json={"assigned_to": str(stranger.id)}).status_code == 422


def test_review_state_and_pending_are_search_columns(client, db):
    """One state per document, filterable and sortable, with the breakdown still in the row (review-ux AC-01)."""
    setup_admin(client, db)
    kho = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    upload(client, "m.docx", sample("de-mau-toan10.docx"))
    run_jobs()
    s = lambda **b: client.post("/api/review/documents/search", json=b)  # noqa: E731
    names = lambda r: [x["document"]["filename"] for x in r.json()["data"]]  # noqa: E731
    rows = {r["document"]["filename"]: r for r in s().json()["data"]}
    k, m = rows["k.docx"], rows["m.docx"]
    assert k["review_state"] == "pending" and k["pending"] == 8 and k["counts"]["needs_review"] == 8
    assert m["review_state"] == "pending"
    assert m["pending"] == m["counts"]["needs_review"] + m["counts"]["flagged"] + m["spot_pending"] and m["spot_pending"] == 2
    # decide every question of k.docx: it leaves the queue without a single count disappearing from the row
    ids = [q["id"] for q in client.get(f"/api/review/documents/{kho}/queue").json()]
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"status": "rejected"}}).json()["updated"] == 8
    done = next(r for r in s().json()["data"] if r["document"]["filename"] == "k.docx")
    assert done["review_state"] == "done" and done["pending"] == 0 and done["counts"]["rejected"] == 8 and done["progress"] == 1.0
    assert names(s(filters={"review_state": {"value": "pending"}})) == ["m.docx"]
    assert names(s(filters={"review_state": {"value": ["done", "in_progress"]}})) == ["k.docx"]
    assert names(s(filters={"pending": {"operator": ">", "value": 0}})) == ["m.docx"]
    assert names(s(filters={"pending": {"from": 0, "to": 0}})) == ["k.docx"]
    assert names(s(sort=[{"field": "review_state"}])) == ["k.docx", "m.docx"]  # done, in_progress, pending
    assert names(s(sort=[{"field": "pending", "desc": True}])) == ["m.docx", "k.docx"]
    # the progress bar is sortable too: k.docx is finished (1.0), m.docx is part-way. A list where every row
    # reads "95%" at a glance is exactly where sorting by the bar earns its place.
    assert names(s(sort=[{"field": "progress"}])) == ["m.docx", "k.docx"]
    assert names(s(sort=[{"field": "progress", "desc": True}])) == ["k.docx", "m.docx"]
    # but not filterable — a float ratio is not something anyone types a bound for
    bad = s(filters={"progress": {"operator": ">", "value": 0.5}})
    assert bad.status_code == 422 and bad.json()["code"] == "bad_filter"
    r = s(filters={"review_state": {"value": "xong"}})
    assert r.status_code == 422 and r.json()["code"] == "bad_filter" and "xong" in r.json()["message"]


def test_students_and_other_orgs(client, db):
    setup_admin(client, db)
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]["id"]
    run_jobs()
    s = client.__class__(client.app)
    org = make_org(db, "orgb")
    make_user(db, org, "gvb", role="teacher")
    db.commit()
    s.post("/api/auth/login", json={"org_code": "orgb", "username": "gvb", "password": "Secret123!"})
    assert s.post("/api/review/documents/search", json={}).json()["data"] == []
    assert s.get(f"/api/review/documents/{doc}").status_code == 404
