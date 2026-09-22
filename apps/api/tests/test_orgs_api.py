from sqlalchemy import func, select

from app.modules.audit.domain.entities import AuditEntry

from app.modules.identity.domain.entities import Organization, User

from app.modules.taxonomy.domain.topics import Topic
from tests.factories import PASSWORD, login_as, make_org, make_user


def create(client, code="TrungtamA", name="Trung tâm A", **kw):
    return client.post("/api/admin/orgs", json={"code": code, "name": name, **kw})


def test_create_org_seeds_and_returns_temp_password(client, db):
    login_as(client, db)
    r = create(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["org"]["code"] == "trungtama"
    assert body["admin"]["username"] == "admin" and len(body["admin"]["temp_password"]) == 10
    org_id = body["org"]["id"]
    assert db.scalar(select(func.count()).select_from(Topic).where(Topic.organization_id == org_id)) > 50
    admin = db.scalar(select(User).where(User.organization_id == org_id))
    assert admin.role == "org_admin" and admin.must_change_password
    assert db.scalar(select(func.count()).select_from(AuditEntry).where(AuditEntry.action == "org.create")) == 1
    # the new admin can log in with the temp password
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"org_code": "TRUNGTAMA", "username": "admin", "password": body["admin"]["temp_password"]})
    assert r.status_code == 200 and r.json()["must_change_password"] is True


def test_duplicate_and_invalid_code(client, db):
    login_as(client, db)
    assert create(client).status_code == 201
    r = create(client, "TRUNGTAMA")
    assert r.status_code == 409 and "code" in r.json()["details"]["fields"]
    r = create(client, "trung tam!")
    assert r.status_code == 422 and "code" in r.json()["details"]["fields"]
    assert db.scalar(select(func.count()).select_from(Organization)) == 2  # system + trungtama


def test_list_search_edit(client, db):
    login_as(client, db)
    oid = create(client).json()["org"]["id"]
    create(client, "trungtamb", "Trung tâm B")
    items = client.post("/api/admin/orgs/search", json={"q": "tâm b"}).json()["data"]
    assert [o["code"] for o in items] == ["trungtamb"]
    r = client.patch(f"/api/admin/orgs/{oid}", json={"name": "Trung tâm A mới", "code": "tta"})
    assert r.status_code == 200 and r.json()["code"] == "tta" and r.json()["name"] == "Trung tâm A mới"
    assert client.patch(f"/api/admin/orgs/{oid}", json={"code": "trungtamb"}).status_code == 409


def test_suspend_activate_delete(client, db):
    root = login_as(client, db)
    org = make_org(db, "ttx")
    make_user(db, org, "hs01")
    db.commit()
    assert client.post(f"/api/admin/orgs/{org.id}/suspend").json()["status"] == "suspended"
    other = client.__class__(client.app)
    r = other.post("/api/auth/login", json={"org_code": "ttx", "username": "hs01", "password": PASSWORD})
    assert r.status_code == 403 and r.json()["message"] == "Tổ chức đang bị khóa"
    client.post(f"/api/admin/orgs/{org.id}/activate")
    assert other.post("/api/auth/login", json={"org_code": "ttx", "username": "hs01", "password": PASSWORD}).status_code == 200
    assert client.delete(f"/api/admin/orgs/{org.id}").status_code == 204
    codes = [o["code"] for o in client.post("/api/admin/orgs/search", json={}).json()["data"]]
    assert "ttx" not in codes
    assert "ttx" in [o["code"] for o in client.post("/api/admin/orgs/search", json={"include_deleted": True}).json()["data"]]
    # hard delete refused while it has students
    assert client.delete(f"/api/admin/orgs/{org.id}", params={"hard": True}).status_code == 409
    system_id = root.organization_id
    assert client.post(f"/api/admin/orgs/{system_id}/suspend").status_code == 403
    assert client.delete(f"/api/admin/orgs/{system_id}").status_code == 403


def test_hard_delete_empty_org(client, db):
    login_as(client, db)
    oid = create(client).json()["org"]["id"]
    assert client.delete(f"/api/admin/orgs/{oid}", params={"hard": True}).status_code == 204
    assert db.get(Organization, oid) is None


def test_only_super_admin(client, db):
    for role in ("org_admin", "teacher", "student"):
        client.cookies.clear()
        org = make_org(db, f"org-{role.replace('_', '')}")
        login_as(client, db, role, org=org)
        assert client.post("/api/admin/orgs/search", json={}).status_code == 403
        assert create(client, f"x{role.replace('_', '')}").status_code == 403
