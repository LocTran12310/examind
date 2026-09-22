"""School structure: levels › grades › classes (school-structure-multi-org US-01, US-02)."""
from sqlalchemy import select

from app.models import Grade, Organization, SchoolClass, SchoolLevel
from tests.factories import login_as


def _levels(db, org_id):
    return {lv.code: lv for lv in db.scalars(select(SchoolLevel).where(SchoolLevel.organization_id == org_id))}


def test_new_org_gets_thcs_and_thpt_with_grades(client, db):
    login_as(client, db)
    r = client.post("/api/admin/orgs", json={"code": "ttc", "name": "Trung tâm C", "admin_username": "admin", "admin_full_name": "A"})
    org_id = r.json()["org"]["id"]
    levels = _levels(db, org_id)
    assert {c: (lv.grade_from, lv.grade_to) for c, lv in levels.items()} == {"thcs": (6, 9), "thpt": (10, 12)}
    grades = {g.level: g.school_level_id for g in db.scalars(select(Grade).where(Grade.organization_id == org_id))}
    assert grades[7] == levels["thcs"].id and grades[11] == levels["thpt"].id and len(grades) == 7


def test_seed_keeps_what_the_org_deleted(client, db):
    from app.seed.org_template import seed_org

    admin = login_as(client, db, "org_admin")
    org = db.get(Organization, admin.organization_id)
    seed_org(db, org.id)
    g6 = db.scalar(select(Grade).where(Grade.organization_id == org.id, Grade.level == 6))
    db.delete(g6)
    db.commit()
    seed_org(db, org.id)
    db.commit()
    assert db.scalar(select(Grade).where(Grade.organization_id == org.id, Grade.level == 6)) is None


def _admin_client(client, db):
    admin = login_as(client, db, "org_admin")
    from app.seed.org_template import seed_org

    seed_org(db, admin.organization_id)
    db.commit()
    return admin


def test_level_and_grade_crud_with_guards(client, db):
    _admin_client(client, db)
    levels = {lv["code"]: lv for lv in client.get("/api/school-levels").json()["items"]}
    assert levels["thcs"]["grade_count"] == 4 and levels["thpt"]["grade_count"] == 3
    # overlapping ranges and bad ranges are refused
    r = client.post("/api/school-levels", json={"code": "th", "name": "Tiểu học", "grade_from": 5, "grade_to": 6})
    assert r.status_code == 422 and "trùng" in r.json()["message"]
    th = client.post("/api/school-levels", json={"code": "TH", "name": "Tiểu học", "grade_from": 1, "grade_to": 5}).json()
    assert th["code"] == "th"
    g1 = client.post("/api/grades", json={"level": 1, "school_level_id": th["id"]}).json()
    assert g1["name"] == "Lớp 1"
    assert client.post("/api/grades", json={"level": 7, "school_level_id": th["id"]}).status_code == 422  # outside 1–5
    assert client.post("/api/grades", json={"level": 1, "school_level_id": th["id"]}).status_code == 409  # duplicate
    r = client.delete(f"/api/school-levels/{th['id']}")
    assert r.status_code == 409 and r.json()["message"] == "Cấp học còn 1 khối"
    klass = client.post("/api/classes", json={"name": "1A", "grade_id": g1["id"]}).json()
    assert (klass["grade"], klass["grade_id"]) == (1, g1["id"])
    r = client.delete(f"/api/grades/{g1['id']}")
    assert r.status_code == 409 and r.json()["message"] == "Khối còn 1 lớp"
    assert client.get("/api/grades", params={"school_level_id": th["id"]}).json()["items"][0]["class_count"] == 1
    # renumbering a grade keeps the class cache in step
    client.patch(f"/api/grades/{g1['id']}", json={"level": 2})
    assert client.get(f"/api/classes/{klass['id']}").json()["grade"] == 2


def test_class_by_grade_number_links_the_grade_and_tree_counts(client, db):
    admin = _admin_client(client, db)
    k = client.post("/api/classes", json={"name": "10A1", "grade": 10}).json()
    g10 = db.scalar(select(Grade).where(Grade.organization_id == admin.organization_id, Grade.level == 10))
    assert k["grade_id"] == str(g10.id)
    from tests.factories import make_user

    s = make_user(db, admin.organization, "hs01")
    db.commit()
    client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(s.id)]})
    client.post("/api/classes", json={"name": "Lớp hè"})
    t = client.get("/api/structure").json()
    thpt = next(lv for lv in t["levels"] if lv["code"] == "thpt")
    assert (thpt["class_count"], thpt["student_count"]) == (1, 1)
    k10 = next(g for g in thpt["grades"] if g["level"] == 10)
    assert k10["classes"][0]["name"] == "10A1" and k10["classes"][0]["member_count"] == 1
    assert [c["name"] for c in t["unassigned"]] == ["Lớp hè"]
    assert client.get("/api/classes", params={"grade_id": str(g10.id)}).json()["total"] == 1


def test_only_org_admin_edits_structure(client, db):
    login_as(client, db, "teacher")
    assert client.get("/api/structure").status_code == 200
    r = client.post("/api/school-levels", json={"code": "x", "name": "X", "grade_from": 1, "grade_to": 2})
    assert r.status_code == 403
