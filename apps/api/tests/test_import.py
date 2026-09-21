import io
import os

from openpyxl import Workbook

from tests.factories import login_as

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples")


def upload(client, name, data: bytes):
    return client.post("/api/users/import/preview", files={"file": (name, data, "text/csv")})


def sample(name):
    with open(os.path.join(SAMPLES, name), "rb") as fh:
        return fh.read()


def test_preview_and_commit_30_students(client, db):
    login_as(client, db, "org_admin", username="admin")
    r = upload(client, "students-30.csv", sample("students-30.csv"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["valid_count"] == 30 and body["error_count"] == 0
    usernames = [row["username"] for row in body["rows"]]
    assert len(set(usernames)) == 30
    assert all(u.isascii() for u in usernames)
    r = client.post("/api/users/import/commit", json={"rows": body["rows"]})
    assert r.status_code == 201, r.text
    created = r.json()["created"]
    assert len(created) == 30 and all(len(c["temp_password"]) == 10 for c in created)
    classes = {c["name"]: c["member_count"] for c in client.get("/api/classes").json()}
    assert classes == {"10A1": 15, "10A2": 15}
    # an imported student must change the password on first login
    first = created[0]
    student = client.__class__(client.app)
    r = student.post("/api/auth/login", json={"org_code": "trungtama", "username": first["username"], "password": first["temp_password"]})
    assert r.status_code == 200 and r.json()["must_change_password"] is True


def test_bad_rows_reported_and_nothing_created(client, db):
    login_as(client, db, "org_admin", username="admin")
    body = upload(client, "students-bad.csv", sample("students-bad.csv")).json()
    errors = {row["row"]: row["errors"] for row in body["rows"] if row["errors"]}
    assert set(errors) == {7, 9, 10}
    assert "Thiếu họ tên" in errors[7]
    assert "Tên đăng nhập đã tồn tại" in errors[9]
    before = client.get("/api/users").json()["total"]
    r = client.post("/api/users/import/commit", json={"rows": body["rows"]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "import_invalid"
    assert client.get("/api/users").json()["total"] == before


def test_xlsx_bom_and_duplicates_in_file(client, db):
    login_as(client, db, "org_admin")
    wb = Workbook()
    ws = wb.active
    ws.append(["Họ tên", "Tên đăng nhập", "Vai trò"])
    ws.append(["Lê An", "lean", "hs"])
    ws.append(["Lê An", "", "gv"])
    ws.append(["Lê Anh", "lean", "hs"])
    buf = io.BytesIO()
    wb.save(buf)
    body = client.post("/api/users/import/preview", files={"file": ("a.xlsx", buf.getvalue(), "application/octet-stream")}).json()
    rows = body["rows"]
    assert rows[0]["errors"] == [] and rows[0]["role"] == "student"
    assert rows[1]["role"] == "teacher" and rows[1]["username"] == "lean2"
    assert "Tên đăng nhập bị trùng trong file" in rows[2]["errors"]
    r = upload(client, "bom.csv", "﻿full_name\nNguyễn Văn An\n".encode("utf-8"))
    assert r.json()["rows"][0]["username"] == "nguyenvanan"


def test_teacher_cannot_import_teachers(client, db):
    login_as(client, db, "teacher")
    body = upload(client, "t.csv", "full_name,role\nA B C,teacher\n".encode()).json()
    assert body["rows"][0]["errors"] == ["Bạn không có quyền tạo vai trò này"]
