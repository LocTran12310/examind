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
