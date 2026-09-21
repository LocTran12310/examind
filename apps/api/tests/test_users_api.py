from app.services.users import base_username
from tests.factories import PASSWORD, login_as, make_org, make_user


def test_base_username_strips_diacritics():
    assert base_username("Nguyễn Văn An") == "nguyenvanan"
    assert base_username("Đặng Thị Ánh") == "dangthianh"


def test_create_edit_deactivate_teacher(client, db):
    login_as(client, db, "org_admin")
    r = client.post("/api/users", json={"full_name": "Trần Thị Bình", "role": "teacher"})
    assert r.status_code == 201, r.text
    body = r.json()
    uid, username, temp = body["user"]["id"], body["user"]["username"], body["temp_password"]
    assert username == "tranthibinh" and len(temp) == 10 and body["user"]["must_change_password"]
    r = client.patch(f"/api/users/{uid}", json={"full_name": "Trần Thị Bình B"})
    assert r.json()["full_name"] == "Trần Thị Bình B"
    assert client.patch(f"/api/users/{uid}", json={"is_active": False}).json()["is_active"] is False
    other = client.__class__(client.app)
    r = other.post("/api/auth/login", json={"org_code": "trungtama", "username": username, "password": temp})
    assert r.status_code == 401


def test_username_collision_gets_suffix(client, db):
    login_as(client, db, "org_admin")
    a = client.post("/api/users", json={"full_name": "Lê An"}).json()["user"]["username"]
    b = client.post("/api/users", json={"full_name": "Lê An"}).json()["user"]["username"]
    assert (a, b) == ("lean", "lean2")
    r = client.post("/api/users", json={"full_name": "X", "username": "LEAN"})
    assert r.status_code == 409


def test_list_filters(client, db):
    admin = login_as(client, db, "org_admin")
    org = admin.organization
    make_user(db, org, "gv01", role="teacher", full_name="Giáo viên")
    make_user(db, org, "hs01", full_name="Học sinh Một")
    db.commit()
    r = client.get("/api/users", params={"role": "student"}).json()
    assert [u["username"] for u in r["items"]] == ["hs01"]
    assert client.get("/api/users", params={"q": "giáo"}).json()["total"] == 1


def test_teacher_manages_students_only(client, db):
    teacher = login_as(client, db, "teacher")
    org = teacher.organization
    other_teacher = make_user(db, org, "gv02", role="teacher")
    student = make_user(db, org, "hs01")
    db.commit()
    assert client.post("/api/users", json={"full_name": "GV mới", "role": "teacher"}).status_code == 403
    assert client.post("/api/users", json={"full_name": "HS mới", "role": "student"}).status_code == 201
    assert client.patch(f"/api/users/{other_teacher.id}", json={"full_name": "x"}).status_code == 403
    assert client.post(f"/api/users/{other_teacher.id}/reset-password").status_code == 403
    assert client.post(f"/api/users/{student.id}/reset-password").status_code == 200
    usernames = [u["username"] for u in client.get("/api/users").json()["items"]]
    assert "gv02" not in usernames and "hs01" in usernames


def test_students_cannot_manage(client, db):
    login_as(client, db, "student")
    assert client.get("/api/users").status_code == 403


def test_reset_password_revokes_sessions(client, db):
    login_as(client, db, "org_admin")
    admin_client = client
    org_code = "trungtama"
    hs = client.post("/api/users", json={"full_name": "Học Sinh", "password": PASSWORD}).json()["user"]
    student = client.__class__(client.app)
    assert student.post("/api/auth/login", json={"org_code": org_code, "username": hs["username"], "password": PASSWORD}).status_code == 200
    r = admin_client.post(f"/api/users/{hs['id']}/reset-password")
    temp = r.json()["temp_password"]
    student.cookies.delete("ex_access")
    assert student.post("/api/auth/refresh").status_code == 401
    r = student.post("/api/auth/login", json={"org_code": org_code, "username": hs["username"], "password": temp})
    assert r.status_code == 200 and r.json()["must_change_password"] is True


def test_tenant_isolation(client, db):
    login_as(client, db, "org_admin")
    other = make_org(db, "orgb")
    stranger = make_user(db, other, "hsb")
    db.commit()
    assert client.get(f"/api/users/{stranger.id}").status_code == 404
    assert client.patch(f"/api/users/{stranger.id}", json={"full_name": "x"}).status_code == 404
    assert client.post(f"/api/users/{stranger.id}/reset-password").status_code == 404
    assert all(u["username"] != "hsb" for u in client.get("/api/users").json()["items"])
