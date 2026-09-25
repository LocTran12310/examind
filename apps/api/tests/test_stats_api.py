import time
import uuid

from sqlalchemy import select, text

from app.modules.assessment.domain.entities import AnswerFact
from app.modules.taxonomy.domain.topics import Topic
from tests.exam_helpers import assign, display_key, display_wrong, exam_with_questions, klass_with_student, login


def two_students(client, db):
    admin, exam = exam_with_questions(client, db, mcq=4, tf=1, short=0)
    klass, _ = klass_with_student(client, db, admin, "hs01")
    s2 = klass_with_student(client, db, admin, "hs02")[1]
    client.post(f"/api/classes/{klass['id']}/members", json={"user_ids": [str(s2.id)]})
    a = assign(client, exam["id"], klass["id"])
    for username, right in (("hs01", True), ("hs02", False)):
        s = login(client, "trungtama", username)
        att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
        for q in s.get(f"/api/attempts/{att}").json()["questions"]:
            if q["type"] == "mcq":
                s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q) if right else display_wrong(db, q)})
        s.post(f"/api/attempts/{att}/submit")
    return admin, exam, klass, a


def test_topic_rollup_matches_leaf_sums(client, db):
    admin, _, klass, _ = two_students(client, db)
    rows = client.get("/api/stats/topics", params={"class_id": klass["id"]}).json()
    by_path = {r["path"]: r for r in rows if r["path"]}
    for path, r in by_path.items():
        children = [c for p, c in by_path.items() if p.startswith(path + ".") and p.count(".") == path.count(".") + 1]
        direct = db.scalar(text("select coalesce(sum(max_points),0) from answer_facts where topic_path = cast(:p as ltree)"), {"p": path})
        assert abs(r["max_points"] - (sum(c["max_points"] for c in children) + direct)) < 1e-9
    strands = [r for r in rows if r["depth"] == 1]
    assert strands and all(0 <= (r["ratio"] or 0) <= 1 for r in strands)
    mcq_total = sum(r["max_points"] for r in strands)
    assert mcq_total > 0


def test_groups_and_heatmap(client, db):
    _, _, klass, a = two_students(client, db)
    by_type = {g["key"]: g for g in client.get("/api/stats/groups", params={"by": "type", "assignment_id": a["id"]}).json()}
    assert by_type["mcq"]["answered"] == 8 and by_type["mcq"]["ratio"] == 0.5
    assert client.get("/api/stats/groups", params={"by": "bogus"}).status_code == 422
    hm = client.get("/api/stats/heatmap", params={"class_id": klass["id"], "level": 1}).json()
    assert len(hm["rows"]) == 2 and hm["columns"]
    good = next(r for r in hm["rows"] if r["username"] == "hs01")
    bad = next(r for r in hm["rows"] if r["username"] == "hs02")
    # hs02 got every MCQ wrong; both skipped the true/false question
    assert all(good["cells"][k]["ratio"] >= bad["cells"][k]["ratio"] for k in good["cells"])
    assert any(good["cells"][k]["ratio"] > bad["cells"][k]["ratio"] for k in good["cells"])


def test_assignment_report(client, db):
    _, exam, klass, a = two_students(client, db)
    r = client.get(f"/api/assignments/{a['id']}/report").json()
    assert r["submitted"] == 2 and r["total_students"] == 2
    scores = sorted(s["score10"] for s in r["students"])
    assert scores[0] < scores[1] and r["average"] == round(sum(scores) / 2, 2)
    assert sum(b["count"] for b in r["distribution"]) == 2
    mcq = [q for q in r["questions"] if q["type"] == "mcq"]
    assert all(q["ratio"] == 0.5 and q["top_wrong"]["count"] == 1 for q in mcq)


def test_students_only_see_themselves(client, db):
    admin, _, klass, _ = two_students(client, db)
    s = login(client, "trungtama", "hs02")
    mine = s.get("/api/stats/groups", params={"by": "type"}).json()
    assert next(g for g in mine if g["key"] == "mcq")["ratio"] == 0.0
    spoof = s.get("/api/stats/groups", params={"by": "type", "student_id": str(uuid.uuid4())}).json()
    assert spoof == mine
    assert s.get("/api/stats/heatmap", params={"class_id": klass["id"]}).status_code == 403


def test_report_query_speed(client, db):
    admin, exam, klass, a = two_students(client, db)
    leaf = db.scalar(select(Topic.path).where(Topic.organization_id == admin.organization_id, Topic.name == "Tìm đỉnh và trục đối xứng parabol"))
    att = db.scalar(select(AnswerFact.attempt_id).limit(1))
    db.execute(text("""insert into answer_facts (id, organization_id, attempt_id, exam_id, student_id, question_id, topic_path, tag_ids,
                        qtype, points, max_points, correct_ratio, created_at)
                       select gen_random_uuid(), :o, :att, gen_random_uuid(), gen_random_uuid(), gen_random_uuid(), cast(:p as ltree), '{}',
                              'mcq', (g % 2) * 0.25, 0.25, (g % 2), now()
                         from generate_series(1, 24000) g"""), {"o": admin.organization_id, "att": att, "p": leaf})
    db.commit()
    db.execute(text("analyze answer_facts"))
    t = time.perf_counter()
    assert client.get("/api/stats/topics").status_code == 200
    assert client.get("/api/stats/groups", params={"by": "type"}).status_code == 200
    assert time.perf_counter() - t < 1.0


def test_class_summary_counts_the_class_and_names_where_it_is_weakest(client, db):
    """AC-03. Một lời gọi trả cả bốn nhóm số; các chuyên đề đi qua đúng phép tính của Báo cáo nên hai màn hình
    không thể lệch nhau."""
    admin, exam, klass, a = two_students(client, db)
    got = client.get(f"/api/classes/{klass['id']}/summary").json()

    assert got["assignments"] == 1 and got["sittings"] == 2
    assert got["average"] is not None and 0 <= got["average"] <= 10
    assert len(got["distribution"]) == 10 and sum(got["distribution"]) == 2
    # hai em rơi vào hai cột khác nhau: điều đáng chứng minh là phổ TRẢI RA, không phải cột nào cụ thể.
    # Không em nào đạt 10: helper chỉ trả lời câu trắc nghiệm và bỏ câu đúng/sai, nên em "làm đúng" vẫn mất
    # điểm phần ấy — ghim một cột cụ thể ở đây là ghim một chi tiết của helper, không phải của tính năng.
    assert len([b for b in got["distribution"] if b]) == 2
    assert got["weakest"], "lớp có dữ liệu thì phải nêu được chỗ yếu"
    assert all(w["ratio"] is not None and w["answered"] > 0 for w in got["weakest"])
    assert got["weakest"] == sorted(got["weakest"], key=lambda w: w["ratio"]), "thấp trước"


def test_a_class_nobody_has_sat_says_so_instead_of_showing_zero(client, db):
    """AC-04. `average: null` chứ không phải 0: màn hình phải phân biệt được "chưa đo" với "đo rồi và bằng 0"."""
    admin, exam = exam_with_questions(client, db, mcq=2, tf=0, short=0)
    klass, _ = klass_with_student(client, db, admin, "hs09")
    assign(client, exam["id"], klass["id"])

    got = client.get(f"/api/classes/{klass['id']}/summary").json()
    assert got["assignments"] == 1 and got["sittings"] == 0
    assert got["average"] is None
    assert got["distribution"] == [0] * 10 and got["weakest"] == []


def test_class_summary_counts_only_its_own_class(client, db):
    """`assignment_targets` nối theo lớp, nên bài giao của lớp khác không lọt vào — đúng chỗ script dọn e2e đã
    suýt sai khi tin một bộ lọc mà endpoint không có."""
    admin, exam, klass, _ = two_students(client, db)
    other, _ = klass_with_student(client, db, admin, "hs08")
    assign(client, exam["id"], other["id"])

    assert client.get(f"/api/classes/{klass['id']}/summary").json()["assignments"] == 1
    theirs = client.get(f"/api/classes/{other['id']}/summary").json()
    assert theirs["assignments"] == 1 and theirs["sittings"] == 0
