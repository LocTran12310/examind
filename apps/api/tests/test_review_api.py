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
    k = rows["k.docx"]
    assert k["total"] == 8 and k["counts"]["needs_review"] == 5 and k["counts"]["auto_approved"] == 3
    assert k["spot_pending"] == 1 and 0 < k["progress"] < 1
    assert rows["m.docx"]["total"] == 40
    r = client.patch(f"/api/review/documents/{kho}", json={"assigned_to": str(teacher.id)})
    assert r.status_code == 200 and r.json()["assigned_name"] == teacher.full_name
    t = client.__class__(client.app)
    t.post("/api/auth/login", json={"org_code": "trungtama", "username": "gv", "password": "Secret123!"})
    assert [x["document"]["filename"] for x in t.post("/api/review/documents/search", json={"mine": True}).json()["data"]] == ["k.docx"]
    assert t.patch(f"/api/review/documents/{kho}", json={"assigned_to": None}).status_code == 403
    stranger = make_user(db, make_org(db, "orgb"), "x", role="teacher")
    db.commit()
    assert client.patch(f"/api/review/documents/{kho}", json={"assigned_to": str(stranger.id)}).status_code == 422


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
