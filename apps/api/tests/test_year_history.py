"""Answers remember year, term and classes; reports and the student record use it (school-years US-03, US-04)."""
from sqlalchemy import select

from app.models import AnswerFact, SchoolYear
from tests.exam_helpers import assign, display_key, exam_with_questions, login
from tests.factories import make_user


def _take(client, db, assignment_id, username):
    s = login(client, "trungtama", username)
    att = s.post(f"/api/assignments/{assignment_id}/start").json()["attempt_id"]
    for q in s.get(f"/api/attempts/{att}").json()["questions"]:
        if q["type"] == "mcq":
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q)})
    s.post(f"/api/attempts/{att}/submit")


def test_facts_snapshot_year_term_and_all_classes_and_reports_follow_the_snapshot(client, db):
    admin, exam = exam_with_questions(client, db, mcq=3, tf=0, short=0)
    year = db.scalar(select(SchoolYear).where(SchoolYear.organization_id == admin.organization_id, SchoolYear.status == "active"))
    main = client.post("/api/classes", json={"name": "10A1", "grade": 10}).json()
    extra = client.post("/api/classes", json={"name": "Toán nâng cao 10", "grade": 10}).json()
    s = make_user(db, admin.organization, "lan", full_name="Lan")
    db.commit()
    for k in (main, extra):
        client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(s.id)]})
    a = assign(client, exam["id"], main["id"])
    _take(client, db, a["id"], "lan")
    facts = db.scalars(select(AnswerFact).where(AnswerFact.student_id == s.id)).all()
    assert facts and all(f.school_year_id == year.id for f in facts)
    assert all({str(x) for x in f.class_ids} == {main["id"], extra["id"]} for f in facts)
    assert all(f.term_code in ("hk1", "hk2", None) for f in facts)

    # next year: Lan moves to 11A1; her lớp-10 answers must stay with 10A1
    nxt = client.post("/api/school-years", json={"code": f"{int(year.code[5:])}-{int(year.code[5:]) + 1}"}).json()
    k11 = client.post("/api/classes", json={"name": "11A1", "grade": 11, "school_year_id": nxt["id"]}).json()
    client.post(f"/api/classes/{k11['id']}/members", json={"user_ids": [str(s.id)]})
    by_class = lambda k: sum(r["max_points"] for r in client.get("/api/stats/topics", params={"class_id": k}).json() if r["depth"] == 1)  # noqa: E731
    assert by_class(main["id"]) > 0 and by_class(k11["id"]) == 0
    assert sum(r["max_points"] for r in client.get("/api/stats/topics", params={"school_year_id": nxt["id"]}).json() if r["depth"] == 1) == 0
    other_term = "hk2" if facts[0].term_code == "hk1" else "hk1"
    assert sum(r["max_points"] for r in client.get("/api/stats/topics", params={"term_code": other_term}).json() if r["depth"] == 1) == 0

    rec = client.get(f"/api/students/{s.id}/record").json()
    assert rec["student"]["full_name"] == "Lan"
    codes = [y["year"]["code"] for y in rec["years"]]
    assert codes == [nxt["code"], year.code]
    this = rec["years"][1]
    assert {c["name"] for c in this["classes"]} == {"10A1", "Toán nâng cao 10"} and this["answered"] == 3 and this["ratio"] == 1
    assert this["topics"] and rec["years"][0]["answered"] == 0


def test_record_is_staff_or_the_student_only(client, db):
    admin, _ = exam_with_questions(client, db, mcq=1, tf=0, short=0)
    s1 = make_user(db, admin.organization, "a1")
    s2 = make_user(db, admin.organization, "a2")
    db.commit()
    c = login(client, "trungtama", "a1")
    assert c.get(f"/api/students/{s1.id}/record").status_code == 200
    assert c.get(f"/api/students/{s2.id}/record").status_code == 403
