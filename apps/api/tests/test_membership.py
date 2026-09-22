"""Users in several organisations (school-structure-multi-org US-03, US-04)."""
from app.models import OrganizationMember
from tests.factories import PASSWORD, login_as, make_org, make_user


def _login(client, org, username):
    r = client.post("/api/auth/login", json={"org_code": org, "username": username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()


def _two_orgs(db):
    a = make_org(db, "tta", "Trung tâm A")
    b = make_org(db, "ttb", "Trung tâm B")
    lan = make_user(db, b, "gvlan", role="teacher", full_name="Cô Lan")  # home = B
    db.add(OrganizationMember(user_id=lan.id, organization_id=a.id, role="org_admin"))
    make_user(db, a, "hsa", full_name="Học sinh A")
    make_user(db, b, "hsb", full_name="Học sinh B")
    db.commit()
    return a, b, lan


def test_home_membership_is_created_for_every_account(db):
    org = make_org(db, "ttx")
    u = make_user(db, org, "x1", role="teacher")
    m = db.get(OrganizationMember, (u.id, org.id))
    assert m is not None and m.role == "teacher" and m.is_active
    u.role = "org_admin"
    db.commit()
    db.refresh(m)
    assert m.role == "org_admin"


def test_switch_org_changes_scope_and_role(client, db):
    a, b, _ = _two_orgs(db)
    me = _login(client, "ttb", "gvlan")
    assert (me["org"]["code"], me["role"], me["home_org"]["code"]) == ("ttb", "teacher", "ttb")
    orgs = client.get("/api/me/orgs").json()
    assert [(o["code"], o["role"], o["is_home"]) for o in orgs] == [("ttb", "teacher", True), ("tta", "org_admin", False)]
    assert {u["username"] for u in client.get("/api/users").json()["items"]} >= {"hsb"}
    r = client.post("/api/auth/switch-org", json={"org_id": str(a.id)})
    assert r.status_code == 200 and (r.json()["org"]["code"], r.json()["role"]) == ("tta", "org_admin")
    names = {u["username"] for u in client.get("/api/users").json()["items"]}
    assert "hsa" in names and "hsb" not in names  # no rows from B while A is open
    assert client.get("/api/auth/me").json()["org"]["code"] == "tta"


def test_cannot_switch_without_membership(client, db):
    _, b, _ = _two_orgs(db)
    c = make_org(db, "ttc")
    db.commit()
    _login(client, "tta", "hsa")
    assert client.post("/api/auth/switch-org", json={"org_id": str(c.id)}).status_code == 403
    assert client.post("/api/auth/switch-org", json={"org_id": str(b.id)}).status_code == 403


def test_login_opens_the_last_org_and_removed_membership_is_refused(client, db):
    a, _, lan = _two_orgs(db)
    _login(client, "ttb", "gvlan")
    client.post("/api/auth/switch-org", json={"org_id": str(a.id)})
    client.post("/api/auth/logout")
    assert _login(client, "ttb", "gvlan")["org"]["code"] == "tta"
    # membership disabled while the token for A is still valid → next request refused, refresh lands in B
    m = db.get(OrganizationMember, (lan.id, a.id))
    m.is_active = False
    db.commit()
    assert client.get("/api/users").status_code == 401
    client.cookies.delete("ex_access")
    assert client.post("/api/auth/refresh").status_code == 204
    assert client.get("/api/auth/me").json()["org"]["code"] == "ttb"


def test_suspended_org_is_hidden_and_falls_back_home(client, db):
    a, _, _ = _two_orgs(db)
    _login(client, "ttb", "gvlan")
    client.post("/api/auth/switch-org", json={"org_id": str(a.id)})
    a.status = "suspended"
    db.commit()
    assert client.get("/api/users").status_code == 401
    client.cookies.delete("ex_access")
    client.post("/api/auth/refresh")
    assert client.get("/api/auth/me").json()["org"]["code"] == "ttb"
    assert [o["code"] for o in client.get("/api/me/orgs").json()] == ["ttb"]


def test_super_admin_sees_every_org_and_works_inside_as_org_admin(client, db):
    a, _, _ = _two_orgs(db)
    login_as(client, db)  # super admin in the system org
    codes = [o["code"] for o in client.get("/api/me/orgs").json()]
    assert codes[0] == "system" and {"tta", "ttb"} <= set(codes)
    me = client.post("/api/auth/switch-org", json={"org_id": str(a.id)}).json()
    assert (me["org"]["code"], me["role"], me["is_super"]) == ("tta", "org_admin", True)
    assert "hsa" in {u["username"] for u in client.get("/api/users").json()["items"]}
    assert client.get("/api/admin/orgs").status_code == 200  # still a platform admin
