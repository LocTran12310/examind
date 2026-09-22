"""School years, classes, levels and grades are searched through POST /<resource>/search (architecture-refactor AC-02)."""
from tests.factories import login_as


def _admin(client, db):
    admin = login_as(client, db, "org_admin")
    from app.seed.org_template import seed_org

    seed_org(db, admin.organization_id)
    db.commit()
    return admin


def test_lists_are_search_endpoints_with_typed_filters(client, db):
    _admin(client, db)
    s = lambda path, **b: client.post(f"/api/{path}/search", json=b)  # noqa: E731
    client.post("/api/school-years", json={"code": "2031-2032"})
    years = s("school-years", filters={"status": {"value": ["planning"]}}).json()
    assert set(years) == {"data", "total", "page", "limit"} and [y["code"] for y in years["data"]] == ["2031-2032"]
    assert s("school-years", filters={"start_date": {"from": "2031-09-01", "to": "2031-09-30"}}).json()["total"] == 1
    levels = s("school-levels", sort=[{"field": "grade_count", "desc": True}]).json()["data"]
    assert [lv["code"] for lv in levels] == ["thcs", "thpt"]
    thpt = levels[1]["id"]
    grades = s("grades", school_level_id=thpt, filters={"level": {"operator": ">=", "value": 11}}).json()["data"]
    assert [g["level"] for g in grades] == [11, 12]
    for name, grade in (("10A1", 10), ("11A1", 11)):
        client.post("/api/classes", json={"name": name, "grade": grade})
    assert [c["name"] for c in s("classes", q="11").json()["data"]] == ["11A1"]
    assert s("classes", filters={"name": {"operator": "+", "value": "10"}}).json()["total"] == 1
    assert s("classes", sort=[{"field": "nope"}]).json()["code"] == "bad_sort"
    assert s("grades", filters={"class_count": {"value": 1}}).json()["code"] == "bad_filter"
    assert len(s("classes", limit=1000).json()["data"]) == 2  # pickers ask for everything
    for path in ("school-years", "classes", "school-levels", "grades"):
        assert client.get(f"/api/{path}").status_code in (404, 405), path  # the old GET lists are gone
