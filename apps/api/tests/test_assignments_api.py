from tests.exam_helpers import assign, exam_with_questions, klass_with_student, login


def test_assign_home_and_start(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, student = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"], results_policy="after_submit")
    assert a["students"] == 1
    s = login(client, "trungtama", "hs01")
    home = s.get("/api/me/assignments").json()
    assert [x["state"] for x in home] == ["open"] and home[0]["attempts_left"] == 1
    r = s.post(f"/api/assignments/{a['id']}/start")
    assert r.status_code == 200
    att = r.json()["attempt_id"]
    assert s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"] == att  # resumed
    listed = client.post("/api/assignments/search", json={"filters": {"exam_id": {"value": exam["id"]}}}).json()["data"]
    assert listed[0]["classes"] == [klass["name"]] and listed[0]["students"] == 1


def test_window_and_attempt_limits(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    later = assign(client, exam["id"], klass["id"], open_delta=3600, close_delta=7200)
    s = login(client, "trungtama", "hs01")
    r = s.post(f"/api/assignments/{later['id']}/start")
    assert r.status_code == 409 and r.json()["code"] == "not_open"
    assert s.get("/api/me/assignments").json()[0]["state"] == "upcoming"
    now_a = assign(client, exam["id"], klass["id"])
    att = s.post(f"/api/assignments/{now_a['id']}/start").json()["attempt_id"]
    s.post(f"/api/attempts/{att}/submit")
    r = s.post(f"/api/assignments/{now_a['id']}/start")
    assert r.status_code == 409 and r.json()["code"] == "no_attempts_left"


def test_the_student_side_endpoints_answer_staff(client, db):
    """exam-runner AC-07: roles nest, so a teacher is answered like anyone else — with their own data."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    assert client.get("/api/me/assignments").json() == []  # answered, and nothing of the student's
    assert client.post(f"/api/assignments/{a['id']}/start").status_code == 404  # not targeted; a trial is the way in
    s = login(client, "trungtama", "hs01")
    home = s.get("/api/me/assignments").json()
    assert [x["state"] for x in home] == ["open"]  # the student is untouched
    assert s.post(f"/api/assignments/{a['id']}/start").status_code == 200


def test_validation_and_permissions(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    r = client.post("/api/assignments", json={"exam_id": exam["id"], "open_at": "2026-09-22T10:00:00Z", "close_at": "2026-09-22T09:00:00Z",
                                                "duration_minutes": 10, "class_ids": [klass["id"]]})
    assert r.status_code == 422
    empty = client.post("/api/exams", json={"title": "Trống"}).json()
    assert client.post("/api/assignments", json={"exam_id": empty["id"], "open_at": "2026-09-22T08:00:00Z", "close_at": "2026-09-22T09:00:00Z",
                                                 "duration_minutes": 10, "class_ids": [klass["id"]]}).status_code == 422
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", "hs01")
    assert s.post("/api/assignments/search", json={}).status_code == 403
    outsider = klass_with_student(client, db, admin, "hs02")[1]
    o = login(client, "trungtama", "hs02")
    assert o.post(f"/api/assignments/{a['id']}/start").status_code == 404
    assert outsider  # member of another class only
