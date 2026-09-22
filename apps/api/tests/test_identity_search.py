"""Users, organisations, accounts and memberships are searched through POST /<resource>/search (architecture-refactor AC-02)."""
from tests.factories import login_as, make_org, make_user


def test_users_search_contract(client, db):
    admin = login_as(client, db, "org_admin")
    for u, name, role in (("gv01", "Giáo viên Một", "teacher"), ("hs01", "Học sinh Một", "student"), ("hs02", "Học sinh Hai", "student")):
        make_user(db, admin.organization, u, role=role, full_name=name)
    db.commit()
    s = lambda **b: client.post("/api/users/search", json=b)  # noqa: E731
    body = s(filters={"role": {"value": ["student"]}}, sort=[{"field": "username", "desc": True}]).json()
    assert set(body) == {"data", "total", "page", "limit"} and [u["username"] for u in body["data"]] == ["hs02", "hs01"]
    assert s(filters={"full_name": {"operator": "+", "value": "hoc sinh"}}).json()["total"] == 2
    assert s(filters={"must_change_password": {"value": False}}).json()["total"] == 4
    assert s(filters={"nope": {"value": 1}}).json()["code"] == "bad_filter"
    assert s(sort=[{"field": "password_hash"}]).json()["code"] == "bad_sort"
    assert client.get("/api/users").status_code in (404, 405)  # the old GET list is gone


def test_admin_searches(client, db):
    org = make_org(db, "tta", "Trung tâm A")
    lan = make_user(db, org, "lan", role="teacher", full_name="Cô Lan")
    db.commit()
    login_as(client, db)
    orgs = client.post("/api/admin/orgs/search", json={"filters": {"code": {"value": "tta", "operator": "="}}}).json()
    assert [(o["code"], o["user_count"]) for o in orgs["data"]] == [("tta", 1)]
    accounts = client.post("/api/admin/users/search", json={"sort": [{"field": "org_count", "desc": True}], "q": "lan"}).json()
    assert [(a["username"], a["org_count"]) for a in accounts["data"]] == [("lan", 1)]
    members = client.post(f"/api/admin/orgs/{org.id}/members/search", json={"filters": {"role": {"value": "teacher"}}}).json()
    assert [(m["username"], m["is_home"]) for m in members["data"]] == [("lan", True)]
    mine = client.post(f"/api/admin/users/{lan.id}/memberships/search", json={"filters": {"org_code": {"value": "tt"}}}).json()
    assert [m["org_code"] for m in mine["data"]] == ["tta"]
    assert client.post("/api/admin/users/search", json={"filters": {"org_count": {"value": 1}}}).json()["code"] == "bad_filter"
    for path in ("/api/admin/orgs", "/api/admin/users", f"/api/admin/orgs/{org.id}/members", f"/api/admin/users/{lan.id}/memberships"):
        assert client.get(path).status_code in (404, 405), path
