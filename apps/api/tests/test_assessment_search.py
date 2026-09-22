"""Exams, an exam's questions and assignments moved to `POST …/search` (architecture-refactor UOW-06, ADR-03)."""
from tests.exam_helpers import assign, exam_with_questions, klass_with_student


def test_exam_search_filters_sort_and_page(client, db):
    _, exam = exam_with_questions(client, db, mcq=2, tf=1, short=0)
    for title, grade in (("Kiểm tra 15 phút", 10), ("Đề thi thử THPT", 12)):
        client.post("/api/exams", json={"title": title, "grade": grade})
    body = client.post("/api/exams/search", json={}).json()
    assert set(body) == {"data", "total", "page", "limit"} and body["total"] == 3
    assert [e["title"] for e in body["data"]] == ["Đề thi thử THPT", "Kiểm tra 15 phút", "Kiểm tra"]  # newest first
    assert all(e["questions"] == [] for e in body["data"])
    by_count = client.post("/api/exams/search", json={"sort": [{"field": "question_count", "desc": True}], "limit": 1}).json()
    assert by_count["data"][0]["id"] == exam["id"] and by_count["data"][0]["question_count"] == 3 and by_count["total"] == 3
    assert [e["title"] for e in client.post("/api/exams/search", json={"q": "thpt"}).json()["data"]] == ["Đề thi thử THPT"]
    assert client.post("/api/exams/search", json={"filters": {"grade": {"operator": ">=", "value": 11}}}).json()["total"] == 1
    assert client.post("/api/exams/search", json={"filters": {"source": {"value": ["manual"]}}}).json()["total"] == 3
    second = client.post("/api/exams/search", json={"limit": 2, "page": 2}).json()
    assert [e["title"] for e in second["data"]] == ["Kiểm tra"] and second["page"] == 2
    r = client.post("/api/exams/search", json={"filters": {"question_count": {"value": 1}}})
    assert r.status_code == 422 and r.json()["code"] == "bad_filter"
    assert client.post("/api/exams/search", json={"sort": [{"field": "nope"}]}).json()["code"] == "bad_sort"
    assert client.get("/api/exams").status_code == 405


def test_exam_question_search(client, db):
    _, exam = exam_with_questions(client, db, mcq=3, tf=1, short=1)
    url = f"/api/exams/{exam['id']}/questions/search"
    body = client.post(url, json={"sort": [{"field": "position", "desc": True}], "limit": 2}).json()
    assert body["total"] == 5 and [q["position"] for q in body["data"]] == [5, 4]
    assert client.post(url, json={"filters": {"section": {"value": ["I", "III"]}}}).json()["total"] == 4
    assert client.post(url, json={"filters": {"points": {"from": 0.5}}}).json()["total"] == 2
    assert client.post(url, json={"filters": {"row": {"value": 1}}}).json()["code"] == "bad_filter"
    assert client.get(f"/api/exams/{exam['id']}/questions").status_code == 405
    assert client.post("/api/exams/00000000-0000-0000-0000-000000000000/questions/search", json={}).status_code == 404


def test_assignment_search(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    first = assign(client, exam["id"], klass["id"], title="Giữa kỳ", open_delta=-7200)
    assign(client, exam["id"], klass["id"], title="Cuối kỳ", minutes=90)
    body = client.post("/api/assignments/search", json={}).json()
    assert [a["title"] for a in body["data"]] == ["Cuối kỳ", "Giữa kỳ"]  # newest window first
    assert body["data"][0]["students"] == 1 and body["data"][0]["classes"] == [klass["name"]] and body["data"][0]["submitted"] == 0
    assert client.post("/api/assignments/search", json={"filters": {"duration_minutes": {"operator": ">", "value": 60}}}).json()["total"] == 1
    assert client.post("/api/assignments/search", json={"q": "giua"}).json()["data"][0]["id"] == first["id"]
    assert client.post("/api/assignments/search", json={"sort": [{"field": "students"}]}).json()["code"] == "bad_sort"
    assert client.get("/api/assignments").status_code == 405
