"""Org ↔ user assignment from both admin screens share one rule set (school-years US-06)."""
from tests.factories import login_as, make_org, make_user


def _data(db):
    a = make_org(db, "tta", "Trung tâm A")
    b = make_org(db, "ttb", "Trung tâm B")
    u = make_user(db, a, "lan", role="teacher", full_name="Cô Lan")
    db.commit()
    return a, b, u


def test_org_to_users_and_user_to_orgs_show_the_same_membership(client, db):
    a, b, u = _data(db)
    login_as(client, db)
    r = client.post(f"/api/admin/orgs/{b.id}/members", json={"org_code": "tta", "username": "lan", "role": "student"})
    assert r.status_code == 201 and (r.json()["is_home"], r.json()["home_org_code"]) == (False, "tta")
    mine = client.get(f"/api/admin/users/{u.id}/memberships").json()["items"]
    assert [(m["org_code"], m["role"], m["is_home"]) for m in mine] == [("tta", "teacher", True), ("ttb", "student", False)]
    # change the role from the user side, see it from the org side
    client.patch(f"/api/admin/users/{u.id}/memberships/{b.id}", json={"role": "teacher"})
    members = client.get(f"/api/admin/orgs/{b.id}/members").json()["items"]
    assert [(m["username"], m["role"]) for m in members] == [("lan", "teacher")]
    acc = next(x for x in client.get("/api/admin/users", params={"username": "lan"}).json()["items"])
    assert (acc["home_org_code"], acc["org_count"]) == ("tta", 2)
    # add from the user side, remove from the org side
    c = make_org(db, "ttc", "Trung tâm C")
    db.commit()
    assert client.post(f"/api/admin/users/{u.id}/memberships", json={"org_id": str(c.id), "role": "teacher"}).status_code == 201
    assert client.post(f"/api/admin/users/{u.id}/memberships", json={"org_id": str(c.id), "role": "teacher"}).status_code == 409
    assert client.delete(f"/api/admin/orgs/{c.id}/members/{u.id}").status_code == 204
    assert len(client.get(f"/api/admin/users/{u.id}/memberships").json()["items"]) == 2


def test_home_membership_rules_and_history(client, db):
    a, b, u = _data(db)
    login_as(client, db)
    assert client.delete(f"/api/admin/users/{u.id}/memberships/{a.id}").status_code == 422
    assert client.patch(f"/api/admin/orgs/{a.id}/members/{u.id}", json={"is_active": False}).status_code == 422
    r = client.patch(f"/api/admin/orgs/{a.id}/members/{u.id}", json={"role": "org_admin"})
    assert r.json()["role"] == "org_admin"
    db.refresh(u)
    assert u.role == "org_admin"  # home role mirrored
    client.post(f"/api/admin/orgs/{b.id}/members", json={"org_code": "tta", "username": "lan", "role": "teacher"})
    actions = [e["action"] for e in client.get("/api/audit", params={"target_id": str(u.id)}).json()["items"]]
    assert actions[:2] == ["member.link", "member.update"]
    system = client.get("/api/me/orgs").json()[0]["id"]
    assert client.post(f"/api/admin/users/{u.id}/memberships", json={"org_id": system, "role": "teacher"}).status_code == 422


def test_admin_endpoints_are_super_admin_only(client, db):
    a, _, u = _data(db)
    login_as(client, db, "org_admin", org=a, username="adm")
    assert client.get("/api/admin/users").status_code == 403
    assert client.get(f"/api/admin/orgs/{a.id}/members").status_code == 403
