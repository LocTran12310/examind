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
    classes = {c["name"]: c["member_count"] for c in client.post("/api/classes/search", json={}).json()["data"]}
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
    before = client.post("/api/users/search", json={}).json()["total"]
    r = client.post("/api/users/import/commit", json={"rows": body["rows"]})
    assert r.status_code == 422 and r.json()["code"] == "import_invalid"
    assert client.post("/api/users/search", json={}).json()["total"] == before


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
    r = upload(client, "bom.csv", "﻿full_name\nNguyễn Văn An\n".encode())
    assert r.json()["rows"][0]["username"] == "nguyenvanan"


def test_teacher_cannot_import_teachers(client, db):
    login_as(client, db, "teacher")
    body = upload(client, "t.csv", b"full_name,role\nA B C,teacher\n").json()
    assert body["rows"][0]["errors"] == ["Bạn không có quyền tạo vai trò này"]


def test_a_file_the_export_wrote_reads_back(client, db):
    """The file people re-import is the one the product exported: Vietnamese headers, Vietnamese roles, `;` classes.

    Written as the export writes it, column for column — including the Email column the importer has no use for, to
    pin that an unknown column is ignored rather than shifting the ones after it."""
    login_as(client, db, "org_admin", username="admin")
    data = ("\ufeffHọ tên,Tên đăng nhập,Email,Vai trò,Lớp\n"
            "Lê Thị Mai,lethimai,,Học sinh,\"12X1; 12X2\"\n"
            "Phạm Văn Bình,phamvanbinh,,Giáo viên,\n"
            "Đỗ Quản Trị,doquantri,,Quản trị trung tâm,\n").encode()
    body = upload(client, "nguoi-dung.csv", data).json()
    assert body["error_count"] == 0, body["rows"]
    assert [r["role"] for r in body["rows"]] == ["student", "teacher", "org_admin"]
    assert [r["full_name"] for r in body["rows"]] == ["Lê Thị Mai", "Phạm Văn Bình", "Đỗ Quản Trị"]
    assert body["rows"][0]["class"] == "12X1; 12X2"
    r = client.post("/api/users/import/commit", json={"rows": body["rows"]})
    assert r.status_code == 201, r.text
    counts = {c["name"]: c["member_count"] for c in client.post("/api/classes/search", json={}).json()["data"]}
    assert counts.get("12X1") == 1 and counts.get("12X2") == 1
    assert "12X1; 12X2" not in counts      # one cell, two classes — never one class with a semicolon in its name


def test_unaccented_headers_and_key_headers_both_read(client, db):
    login_as(client, db, "org_admin", username="admin")
    body = upload(client, "a.csv", "Ho ten,Vai tro,Lop\nTrần Bảo,gv,\n".encode()).json()
    assert body["rows"][0]["full_name"] == "Trần Bảo" and body["rows"][0]["role"] == "teacher"
    body = upload(client, "b.csv", "full_name,role,class\nTrần Bảo,teacher,\n".encode()).json()
    assert body["rows"][0]["full_name"] == "Trần Bảo" and body["rows"][0]["role"] == "teacher"
