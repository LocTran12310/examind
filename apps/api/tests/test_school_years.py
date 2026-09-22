"""School years with HK1/HK2 (school-years US-01, US-02)."""
from datetime import date

from app.services.school_years import current_code, default_dates, term_for_date
from tests.factories import login_as


def _admin(client, db):
    admin = login_as(client, db, "org_admin")
    from app.seed.org_template import seed_org

    seed_org(db, admin.organization_id)
    db.commit()
    return admin


def test_org_starts_with_the_current_year_active_and_terms(client, db):
    _admin(client, db)
    years = client.post("/api/school-years/search", json={}).json()["data"]
    assert [(y["code"], y["status"]) for y in years] == [(current_code(), "active")]
    assert [t["code"] for t in years[0]["terms"]] == ["hk1", "hk2"]


def test_create_activate_close_reopen(client, db):
    _admin(client, db)
    old = client.post("/api/school-years/search", json={}).json()["data"][0]
    assert client.post("/api/school-years", json={"code": "2030-2032"}).status_code == 422
    new = client.post("/api/school-years", json={"code": "2031-2032"}).json()
    assert new["status"] == "planning" and new["start_date"] == "2031-09-05"
    assert client.post("/api/school-years", json={"code": "2031-2032"}).status_code == 409
    act = client.post(f"/api/school-years/{new['id']}/activate").json()
    assert act["status"] == "active"
    statuses = {y["code"]: y["status"] for y in client.post("/api/school-years/search", json={}).json()["data"]}
    assert statuses == {old["code"]: "closed", "2031-2032": "active"}
    assert client.post(f"/api/school-years/{old['id']}/reopen").json()["status"] == "planning"
    # term dates must stay inside the year
    bad = client.patch(f"/api/school-years/{new['id']}", json={"terms": [{"code": "hk1", "start_date": "2031-08-01", "end_date": "2032-01-15"}]})
    assert bad.status_code == 422


def test_classes_belong_to_a_year_and_filter_by_it(client, db):
    _admin(client, db)
    cur = client.post("/api/school-years/search", json={}).json()["data"][0]
    nxt = client.post("/api/school-years", json={"code": "2031-2032"}).json()
    a = client.post("/api/classes", json={"name": "10A1"}).json()  # default = active year
    b = client.post("/api/classes", json={"name": "10A1", "grade": 10, "school_year_id": nxt["id"]}).json()
    assert (a["school_year_id"], b["school_year_id"], b["school_year"]) == (cur["id"], nxt["id"], "2031-2032")
    assert client.post("/api/classes/search", json={"school_year_id": nxt["id"]}).json()["total"] == 1
    tree = client.get("/api/structure", params={"school_year_id": nxt["id"]}).json()
    thpt = next(lv for lv in tree["levels"] if lv["code"] == "thpt")
    assert thpt["class_count"] == 1
    assert client.delete(f"/api/school-years/{nxt['id']}").status_code == 409  # still has a class
    # a year string from an old client creates the year on demand
    c = client.post("/api/classes", json={"name": "12C", "school_year": "2029-2030"}).json()
    assert any(y["code"] == "2029-2030" for y in client.post("/api/school-years/search", json={}).json()["data"]) and c["school_year_id"]


def test_closed_year_stays_editable_and_every_change_is_in_the_history(client, db):
    _admin(client, db)
    cur = client.post("/api/school-years/search", json={}).json()["data"][0]
    k = client.post("/api/classes", json={"name": "10A1"}).json()
    client.post(f"/api/school-years/{cur['id']}/close")
    assert client.patch(f"/api/classes/{k['id']}", json={"name": "10A1-CLC"}).status_code == 200
    h = client.get("/api/audit", params={"target_id": k["id"]}).json()
    last = h["items"][0]
    assert last["action"] == "class.update" and last["data"]["closed_year"] is True
    assert last["data"]["changes"] == {"name": ["10A1", "10A1-CLC"]}
    year_h = [e["action"] for e in client.get("/api/audit", params={"target_id": cur["id"]}).json()["items"]]
    assert "year.close" in year_h


def test_teachers_read_years_but_cannot_change_them_or_read_history(client, db):
    login_as(client, db, "teacher")
    assert client.post("/api/school-years/search", json={}).status_code == 200
    assert client.post("/api/school-years", json={"code": "2031-2032"}).status_code == 403
    assert client.get("/api/audit").status_code == 403


def test_date_helpers():
    assert current_code(date(2026, 8, 1)) == "2026-2027" and current_code(date(2027, 5, 1)) == "2026-2027"
    start, end, terms = default_dates("2026-2027")
    assert (start, end) == (date(2026, 9, 5), date(2027, 5, 31)) and terms[1][2] == date(2027, 1, 16)

    from types import SimpleNamespace as NS

    year = NS(terms=[NS(code=c, start_date=s, end_date=e) for c, _, s, e in terms])
    assert term_for_date(year, date(2026, 12, 1)) == "hk1" and term_for_date(year, date(2027, 3, 1)) == "hk2"
