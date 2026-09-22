"""Users in several organisations (school-structure-multi-org US-03, US-04)."""
from app.modules.identity.domain.entities import Membership
from tests.factories import PASSWORD, login_as, make_org, make_user


def _login(client, org, username):
    r = client.post("/api/auth/login", json={"org_code": org, "username": username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()


def _two_orgs(db):
    a = make_org(db, "tta", "Trung tâm A")
    b = make_org(db, "ttb", "Trung tâm B")
    lan = make_user(db, b, "gvlan", role="teacher", full_name="Cô Lan")  # home = B
    db.add(Membership(user_id=lan.id, organization_id=a.id, role="org_admin"))
    make_user(db, a, "hsa", full_name="Học sinh A")
    make_user(db, b, "hsb", full_name="Học sinh B")
    db.commit()
    return a, b, lan


def test_home_membership_is_created_for_every_account(db):
    org = make_org(db, "ttx")
    u = make_user(db, org, "x1", role="teacher")
    m = db.get(Membership, (u.id, org.id))
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
    assert {u["username"] for u in client.post("/api/users/search", json={}).json()["data"]} >= {"hsb"}
    r = client.post("/api/auth/switch-org", json={"org_id": str(a.id)})
    assert r.status_code == 200 and (r.json()["org"]["code"], r.json()["role"]) == ("tta", "org_admin")
    names = {u["username"] for u in client.post("/api/users/search", json={}).json()["data"]}
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
    m = db.get(Membership, (lan.id, a.id))
    m.is_active = False
    db.commit()
    assert client.post("/api/users/search", json={}).status_code == 401
    client.cookies.delete("ex_access")
    assert client.post("/api/auth/refresh").status_code == 204
    assert client.get("/api/auth/me").json()["org"]["code"] == "ttb"


def test_suspended_org_is_hidden_and_falls_back_home(client, db):
    a, _, _ = _two_orgs(db)
    _login(client, "ttb", "gvlan")
    client.post("/api/auth/switch-org", json={"org_id": str(a.id)})
    a.status = "suspended"
    db.commit()
    assert client.post("/api/users/search", json={}).status_code == 401
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
    assert "hsa" in {u["username"] for u in client.post("/api/users/search", json={}).json()["data"]}
    assert client.post("/api/admin/orgs/search", json={}).status_code == 200  # still a platform admin


def test_linked_member_is_listed_with_role_and_home_org(client, db):
    a, b, lan = _two_orgs(db)
    login_as(client, db, "org_admin", org=a, username="admin_a")
    rows = {u["username"]: u for u in client.post("/api/users/search", json={}).json()["data"]}
    assert (rows["gvlan"]["role"], rows["gvlan"]["is_home"], rows["gvlan"]["home_org_code"]) == ("org_admin", False, "ttb")
    assert rows["hsa"]["is_home"] is True and "hsb" not in rows
    assert client.post("/api/users/search", json={"filters": {"role": {"value": "org_admin"}}}).json()["total"] == 2  # admin_a + gvlan (role in A)
    # A cannot reset the password or rename an account it does not own
    assert client.post(f"/api/users/{lan.id}/reset-password").status_code == 403
    assert client.patch(f"/api/users/{lan.id}", json={"full_name": "X"}).status_code == 403
    # but can change the role in A and lock access to A only
    assert client.patch(f"/api/users/{lan.id}", json={"role": "teacher"}).json()["role"] == "teacher"
    assert client.patch(f"/api/users/{lan.id}", json={"is_active": False}).json()["is_active"] is False
    db.refresh(lan)
    assert lan.is_active and lan.role == "teacher"  # home account untouched


def test_per_org_roles_in_checks(client, db):
    """AC-13: a teacher in A who is a student in B."""
    a, b, _ = _two_orgs(db)
    minh = make_user(db, b, "minh", role="student", full_name="Minh")
    db.add(Membership(user_id=minh.id, organization_id=a.id, role="teacher"))
    db.commit()
    login_as(client, db, "org_admin", org=a, username="admin_a")
    doc_ok = client.post("/api/users/search", json={"filters": {"role": {"value": "teacher"}}}).json()["data"]
    assert [u["username"] for u in doc_ok] == ["minh"]
    k = client.post("/api/classes", json={"name": "10A1"}).json()
    # hsb is not a member of A → cannot join A's class
    from sqlalchemy import select

    from app.modules.identity.domain.entities import User

    hsb_id = db.scalar(select(User.id).where(User.username == "hsb"))
    assert client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(hsb_id)]}).status_code == 404
    assert client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(minh.id)]}).status_code == 204


def test_link_and_unlink_an_account(client, db):
    a, b, _ = _two_orgs(db)
    make_user(db, b, "gvhoa", role="teacher", full_name="Cô Hoa")
    db.commit()
    login_as(client, db, "org_admin", org=a, username="admin_a")
    assert client.post("/api/users/link", json={"org_code": "ttb", "username": "nobody", "role": "teacher"}).status_code == 404
    r = client.post("/api/users/link", json={"org_code": "TTB", "username": "gvhoa", "role": "teacher"})
    assert r.status_code == 201 and (r.json()["is_home"], r.json()["role"]) == (False, "teacher")
    assert client.post("/api/users/link", json={"org_code": "ttb", "username": "gvhoa", "role": "teacher"}).status_code == 409
    hoa = r.json()["id"]
    k = client.post("/api/classes", json={"name": "10A9"}).json()
    client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [hoa]})
    # Hoa can now switch to A
    hoa_client = client.__class__(client.app)
    _login(hoa_client, "ttb", "gvhoa")
    assert "tta" in [o["code"] for o in hoa_client.get("/api/me/orgs").json()]
    assert hoa_client.post("/api/auth/switch-org", json={"org_id": str(a.id)}).status_code == 200
    # unlink: access to A ends, A's class memberships go, the account still works in B
    assert client.delete(f"/api/users/{hoa}/membership").status_code == 204
    assert client.get(f"/api/classes/{k['id']}").json()["member_count"] == 0
    assert hoa_client.post("/api/users/search", json={}).status_code == 401
    hoa_client.cookies.delete("ex_access")
    assert hoa_client.post("/api/auth/refresh").status_code == 204
    assert hoa_client.get("/api/auth/me").json()["org"]["code"] == "ttb"
    # the home membership cannot be removed
    hsa = next(u["id"] for u in client.post("/api/users/search", json={}).json()["data"] if u["username"] == "hsa")
    assert client.delete(f"/api/users/{hsa}/membership").status_code == 422


def test_teachers_cannot_link(client, db):
    a, _, _ = _two_orgs(db)
    login_as(client, db, "teacher", org=a, username="gv_a")
    assert client.post("/api/users/link", json={"org_code": "ttb", "username": "gvlan", "role": "teacher"}).status_code == 403
