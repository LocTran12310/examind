from sqlalchemy import select

from app.modules.taxonomy.domain.topics import Topic
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin


def bank_ready(client, db):
    admin = setup_admin(client, db)
    for name in ("de-mau-toan10.docx", "de-thpt2025-toan.docx"):
        upload(client, name, sample(name))
    run_jobs()
    topics = {t.name: str(t.id) for t in db.scalars(select(Topic).where(Topic.organization_id == admin.organization_id))}
    return admin, topics


def test_blueprint_draws_distinct_questions_and_reports_shortfalls(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Kiểm tra 15 phút"}).json()
    # a mức độ row used to find nothing at all — the pipeline never wrote one — so it was short by its whole count.
    # Since difficulty-at-upload every parsed question carries a level, and what the row asks for is what is there
    graded = client.post("/api/questions/search", json={"topic_id": t["Đại số"], "type": "mcq", "difficulty": "vdc",
                                                        "status": "usable", "limit": 1}).json()["total"]
    assert graded > 0
    rows = [{"topic_id": t["Đại số"], "type": "mcq", "difficulty": "vdc", "count": 50},
            {"topic_id": t["Đại số"], "type": "mcq", "count": 6}, {"topic_id": t["Hình học"], "type": "mcq", "count": 4}]
    r = client.post(f"/api/exams/{exam['id']}/blueprint", json={"rows": rows, "seed": 1}).json()
    assert r["added"] == graded + 10 and r["shortfalls"] == [{"row": 0, "missing": 50 - graded}]
    e = r["exam"]
    ids = [q["id"] for q in e["questions"]]
    assert len(set(ids)) == r["added"] and e["total_points"] == r["added"] * 0.25
    assert [q["position"] for q in e["questions"]] == list(range(1, r["added"] + 1))
    assert all(q["section"] == "I" and q["answer"] for q in e["questions"])


def test_blueprint_refuses_a_row_on_a_topic_with_no_usable_question(client, db):
    """pickers-builder AC-06 (A-05): the row is named with what its topic holds, and nothing is generated."""
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Đề ma trận"}).json()
    rows = [{"topic_id": t["Đại số"], "type": "mcq", "count": 2}, {"topic_id": t["Xác suất"], "count": 3}]
    r = client.post(f"/api/exams/{exam['id']}/blueprint", json={"rows": rows, "seed": 1})
    assert r.status_code == 422 and r.json()["code"] == "empty_topic"
    fields = r.json()["details"]["fields"]
    assert (fields["row"], fields["topic_id"], fields["topic_name"], fields["question_count"]) == (1, t["Xác suất"], "Xác suất", 0)
    assert "Xác suất" in r.json()["message"]
    assert client.post(f"/api/exams/{exam['id']}/questions/search", json={}).json()["total"] == 0
    kept = client.post(f"/api/exams/{exam['id']}/blueprint", json={"rows": rows[:1], "seed": 1}).json()
    assert kept["added"] == 2 and kept["shortfalls"] == []


def test_manual_edits_points_and_sections(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Đề hỗn hợp"}).json()
    tf = client.post("/api/questions/search", json={"type": "true_false"}).json()["data"][:2]
    mcq = client.post("/api/questions/search", json={"type": "mcq", "q": "parabol"}).json()["data"][:2]
    e = client.post(f"/api/exams/{exam['id']}/questions", json={"question_ids": [x["id"] for x in tf + mcq]}).json()
    assert [q["section"] for q in e["questions"]] == ["I", "I", "II", "II"] and e["total_points"] == 2.5
    e = client.patch(f"/api/exams/{exam['id']}", json={"settings": {"points_by_type": {"mcq": 0.5}}}).json()
    assert e["total_points"] == 3.0
    first = e["questions"][0]["id"]
    e = client.patch(f"/api/exams/{exam['id']}/questions/{first}", json={"points": 2}).json()
    assert e["total_points"] == 4.5
    order = [q["id"] for q in e["questions"]][::-1]
    assert [q["id"] for q in client.put(f"/api/exams/{exam['id']}/order", json={"question_ids": order}).json()["questions"]] == order
    e = client.delete(f"/api/exams/{exam['id']}/questions/{first}").json()
    assert e["question_count"] == 3
    swapped = client.post(f"/api/exams/{exam['id']}/questions/{order[0]}/swap").json()
    assert order[0] not in [q["id"] for q in swapped["questions"]] and swapped["question_count"] == 3


def test_question_in_exam_cannot_be_deleted_and_list(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Đề"}).json()
    q = client.post("/api/questions/search", json={}).json()["data"][0]
    client.post(f"/api/exams/{exam['id']}/questions", json={"question_ids": [q["id"]]})
    r = client.delete(f"/api/questions/{q['id']}")
    assert r.status_code == 409 and r.json()["code"] == "question_in_use"
    listed = client.post("/api/exams/search", json={}).json()["data"]
    assert listed[0]["question_count"] == 1 and listed[0]["questions"] == []
    assert client.post("/api/exams", json={"title": " "}).status_code == 422


def test_exam_questions_are_a_paged_table(client, db):
    from tests.exam_helpers import exam_with_questions

    _, exam = exam_with_questions(client, db, mcq=4, tf=1, short=1)
    r = client.post(f"/api/exams/{exam['id']}/questions/search", json={"limit": 3}).json()
    assert r["total"] == 6 and [q["position"] for q in r["data"]] == [1, 2, 3]
    assert {"stem", "options", "points", "section", "topics"} <= set(r["data"][0])
    only_tf = client.post(f"/api/exams/{exam['id']}/questions/search", json={"filters": {"type": {"value": "true_false"}}}).json()
    assert only_tf["total"] == 1 and only_tf["data"][0]["section"] == "II"
    assert client.post("/api/exams/search", json={"limit": 5}).json()["data"][0]["questions"] == []  # the list never embeds questions


def test_subject_and_grade_can_be_set_and_cleared(client, db):
    """A label the screen offers to empty must actually empty (AC-12).

    `PATCH` builds its changes with `exclude_unset=True`, so a key that arrives at all was sent deliberately and
    `null` means "clear". Reading truthiness instead of presence made "Chưa chọn" a silent no-op — the exam kept
    the old grade and the screen went on showing it.
    """
    setup_admin(client, db)
    subject = client.get("/api/taxonomy").json()["subjects"][0]["id"]
    exam = client.post("/api/exams", json={"title": "Đề nhãn", "subject_id": subject, "grade": 11}).json()
    assert exam["subject_id"] == subject and exam["grade"] == 11
    # a change that says nothing about the labels leaves them alone
    assert client.patch(f"/api/exams/{exam['id']}", json={"title": "Đề nhãn 2"}).json()["grade"] == 11
    # and one that sends null clears them
    cleared = client.patch(f"/api/exams/{exam['id']}", json={"grade": None, "subject_id": None}).json()
    assert cleared["grade"] is None and cleared["subject_id"] is None
