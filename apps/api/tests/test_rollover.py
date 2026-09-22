"""Chuyển năm học (school-years US-05)."""
from sqlalchemy import select

from app.modules.academic.domain.entities import ClassMember, SchoolClass
from tests.factories import login_as, make_user


def _setup(client, db):
    admin = login_as(client, db, "org_admin")
    from app.seed.org_template import seed_org

    seed_org(db, admin.organization_id)
    db.commit()
    year = client.post("/api/school-years/search", json={}).json()["data"][0]
    people = {}
    for cname, grade, names in (("10A1", 10, ["an", "binh", "chi"]), ("11B", 11, ["dung"]), ("12C", 12, ["em"])):
        k = client.post("/api/classes", json={"name": cname, "grade": grade}).json()
        for n in names:
            people[n] = make_user(db, admin.organization, n, full_name=n.upper())
        db.commit()
        client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(people[n].id) for n in names]})
    return admin, year, people


def test_preview_maps_classes_and_defaults(client, db):
    _, year, _ = _setup(client, db)
    p = client.post(f"/api/school-years/{year['id']}/rollover/preview", json={}).json()
    nxt = f"{year['code'][5:]}-{int(year['code'][5:]) + 1}"
    assert p["target_code"] == nxt and p["top_grade"] == 12
    m = {c["source_name"]: c for c in p["classes"]}
    assert (m["10A1"]["target_name"], m["11B"]["target_name"], m["12C"]["graduating"]) == ("11A1", "12B", True)
    assert {s["action"] for s in m["10A1"]["students"]} == {"promote"} and m["12C"]["students"][0]["action"] == "graduate"
    assert client.post(f"/api/school-years/{year['id']}/rollover/preview", json={"target_code": year["code"]}).status_code == 422


def test_commit_with_exceptions_is_idempotent_and_can_activate(client, db):
    _, year, people = _setup(client, db)
    p = client.post(f"/api/school-years/{year['id']}/rollover/preview", json={}).json()
    for c in p["classes"]:
        for s in c["students"]:
            if s["username"] == "binh":
                s["action"] = "retain"
            if s["username"] == "chi":
                s["action"] = "transfer"
    body = {"target_code": p["target_code"], "classes": p["classes"], "activate_target": True}
    r = client.post(f"/api/school-years/{year['id']}/rollover/commit", json=body).json()
    assert (r["promote"], r["retain"], r["transfer"], r["graduate"]) == (2, 1, 1, 1)
    assert sorted(r["classes_created"]) == ["10A1", "11A1", "12B"]
    target = r["target_year_id"]
    cls = {c.name: c for c in db.scalars(select(SchoolClass).where(SchoolClass.school_year_id == target))}
    members = lambda k: {m.user_id for m in db.scalars(select(ClassMember).where(ClassMember.class_id == cls[k].id))}  # noqa: E731
    assert members("11A1") == {people["an"].id} and members("10A1") == {people["binh"].id} and members("12B") == {people["dung"].id}
    assert cls["11A1"].grade == 11
    old = {m.user_id: m.status for m in db.scalars(select(ClassMember).join(SchoolClass).where(SchoolClass.school_year_id == year["id"]))}
    assert old[people["an"].id] == "promoted" and old[people["chi"].id] == "transferred" and old[people["em"].id] == "graduated"
    statuses = {y["code"]: y["status"] for y in client.post("/api/school-years/search", json={}).json()["data"]}
    assert statuses[p["target_code"]] == "active" and statuses[year["code"]] == "closed"
    # running again creates nothing new and duplicates nobody
    again = client.post(f"/api/school-years/{year['id']}/rollover/commit", json={**body, "activate_target": False}).json()
    assert again["classes_created"] == []
    assert members("11A1") == {people["an"].id}
    assert "rollover.commit" in [e["action"] for e in client.post("/api/audit/search", json={"target_id": year["id"]}).json()["data"]]


def test_only_org_admin(client, db):
    from app.modules.academic.interface.deps import academic_api

    t = login_as(client, db, "teacher")
    academic = academic_api(db)
    y = academic.ensure_year(t.organization_id, academic.current_code())
    db.commit()
    assert client.post(f"/api/school-years/{y.id}/rollover/preview", json={}).status_code == 403
