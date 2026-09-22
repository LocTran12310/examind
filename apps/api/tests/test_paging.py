"""Server-side list params shared by every data table (ui-shadcn-shell AC-10)."""
from datetime import datetime, timezone

from tests.factories import login_as, make_org, make_user


def _names(r):
    assert r.status_code == 200, r.text
    return [u["full_name"] for u in r.json()["items"]]


def _people(db, org):
    for i, (name, role) in enumerate([("Bùi Văn Châu", "student"), ("Nguyễn Thị Ánh", "student"), ("Trần Bùi Minh", "teacher"),
                                      ("Lê Hoàng", "student"), ("Phạm Văn Bửu", "student")]):
        make_user(db, org, f"u{i}", role=role, full_name=name)
    db.commit()


def test_page_envelope_defaults_to_20(client, db):
    admin = login_as(client, db, "org_admin")
    for i in range(25):
        make_user(db, admin.organization, f"hs{i:02}", full_name=f"Học sinh {i:02}")
    db.commit()
    body = client.get("/api/users").json()
    assert (body["page"], body["page_size"], body["total"], len(body["items"])) == (1, 20, 26, 20)
    second = client.get("/api/users", params={"page": 2}).json()
    assert len(second["items"]) == 6 and not {u["id"] for u in body["items"]} & {u["id"] for u in second["items"]}
    assert client.get("/api/users", params={"page_size": "all"}).json()["page_size"] == 1000


def test_text_filter_is_accent_and_case_insensitive(client, db):
    admin = login_as(client, db, "org_admin")
    _people(db, admin.organization)
    assert sorted(_names(client.get("/api/users", params={"full_name": "bui"}))) == ["Bùi Văn Châu", "Trần Bùi Minh"]
    assert _names(client.get("/api/users", params={"full_name": "ANH"})) == ["Nguyễn Thị Ánh"]
    assert _names(client.get("/api/users", params={"q": "hoang"})) == ["Lê Hoàng"]
    # LIKE metacharacters are literal
    assert _names(client.get("/api/users", params={"full_name": "%"})) == []


def test_exact_bool_and_combined_filters(client, db):
    admin = login_as(client, db, "org_admin")
    _people(db, admin.organization)
    db.execute(__import__("sqlalchemy").text("update users set is_active=false where username='u4'"))
    db.commit()
    assert _names(client.get("/api/users", params={"role": "teacher"})) == ["Trần Bùi Minh"]
    assert len(_names(client.get("/api/users", params={"role": "teacher,org_admin"}))) == 2
    assert _names(client.get("/api/users", params={"is_active": "false"})) == ["Phạm Văn Bửu"]
    assert _names(client.get("/api/users", params={"full_name": "bui", "role": "student"})) == ["Bùi Văn Châu"]


def test_date_range_filter(client, db):
    admin = login_as(client, db, "org_admin")
    old = make_user(db, admin.organization, "old", full_name="Cũ")
    old.created_at = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)
    db.commit()
    assert _names(client.get("/api/users", params={"created_at_from": "2026-01-15", "created_at_to": "2026-01-15"})) == ["Cũ"]
    assert "Cũ" not in _names(client.get("/api/users", params={"created_at_from": "2026-02-01"}))
    assert client.get("/api/users", params={"created_at_from": "15/01/2026"}).status_code == 422


def test_sort_and_bad_sort(client, db):
    admin = login_as(client, db, "org_admin")
    _people(db, admin.organization)
    names = _names(client.get("/api/users", params={"sort": "-username", "role": "student"}))
    assert names == ["Phạm Văn Bửu", "Lê Hoàng", "Nguyễn Thị Ánh", "Bùi Văn Châu"]
    r = client.get("/api/users", params={"sort": "password_hash"})
    assert r.status_code == 422 and r.json()["code"] == "bad_sort"


def test_unknown_params_are_ignored_and_tenancy_kept(client, db):
    admin = login_as(client, db, "org_admin")
    other = make_org(db, "ttb", "Trung tâm B")
    make_user(db, other, "bui", full_name="Bùi Ở Org Khác")
    db.commit()
    assert _names(client.get("/api/users", params={"full_name": "bui", "nonsense": "1"})) == []


def test_orgs_and_classes_are_paged(client, db):
    login_as(client, db)
    for i in range(3):
        client.post("/api/admin/orgs", json={"code": f"tt{i}", "name": f"Trung tâm {i}", "admin_username": "admin", "admin_full_name": "A"})
    body = client.get("/api/admin/orgs", params={"name": "trung tam 1"}).json()
    assert [o["code"] for o in body["items"]] == ["tt1"] and body["total"] == 1
    assert client.get("/api/admin/orgs", params={"status": "suspended"}).json()["total"] == 0

    staff = client.__class__(client.app)
    login_as(staff, db, "org_admin")
    for name, grade in [("10A1", 10), ("11B", 11), ("12C", 12)]:
        staff.post("/api/classes", json={"name": name, "grade": grade})
    body = staff.post("/api/classes/search", json={"filters": {"grade": {"from": 11}}, "sort": [{"field": "name", "desc": True}]}).json()
    assert [c["name"] for c in body["data"]] == ["12C", "11B"] and body["total"] == 2
    assert staff.post("/api/classes/search", json={"sort": [{"field": "member_count", "desc": True}]}).status_code == 200


def test_former_bare_lists_are_paged(client, db):
    login_as(client, db, "org_admin")
    for name in ["Đổi biến số", "Từng phần", "Casio"]:
        client.post("/api/tags", json={"group": "method", "name": name})
    tags = client.post("/api/tags/search", json={"filters": {"name": {"value": "doi bien"}}}).json()
    assert [t["name"] for t in tags["data"]] == ["Đổi biến số"] and tags["total"] == 1
    assert client.post("/api/tags/search", json={"limit": 2}).json()["total"] == 3
    for title in ["Kiểm tra 15 phút", "Đề thi thử THPT"]:
        client.post("/api/exams", json={"title": title})
    exams = client.get("/api/exams", params={"title": "thpt"}).json()
    assert [e["title"] for e in exams["items"]] == ["Đề thi thử THPT"]
    assert client.get("/api/exams", params={"sort": "question_count"}).status_code == 200
    for path in ("/api/assignments", "/api/review/documents", "/api/review/flagged", "/api/ai-models", "/api/documents"):
        body = client.get(path).json()
        assert set(body) == {"items", "total", "page", "page_size"}, path
