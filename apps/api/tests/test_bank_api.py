import time
import uuid

from sqlalchemy import select, text

from app.modules.bank.domain.entities import ReviewEvent
from app.modules.taxonomy.domain.topics import Topic
from tests.factories import make_org, make_user
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin

OPTS = [{"label": l, "content": c} for l, c in zip("ABCD", ["1", "2", "3", "4"])]


def search(client, body: dict | None = None):
    """POST /questions/search: the bank filters sit at the top of the body."""
    return client.post("/api/questions/search", json=body or {})


def loaded(client, db):
    admin = setup_admin(client, db)
    doc = upload(client, "m.docx", sample("de-mau-toan10.docx"), meta={"grade": 10}).json()["document"]["id"]
    run_jobs()
    return admin, doc


def test_search_text_filters_and_topic_subtree(client, db):
    admin, doc = loaded(client, db)
    r = search(client, {"q": "parabol"}).json()
    assert r["total"] >= 5 and all("parabol" in x["stem"] for x in r["data"])
    r = search(client, {"q": "tọa độ đỉnh", "grade": 10}).json()
    assert r["total"] >= 5
    dai_so = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Đại số"))
    leafs = search(client, {"topic_id": str(dai_so.id), "limit": 100}).json()
    names = {x["topics"][0]["name"] for x in leafs["data"]}
    assert "Tìm đỉnh và trục đối xứng parabol" in names and leafs["total"] >= 10
    hinh = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Hình học"))
    assert not ({x["id"] for x in leafs["data"]} & {x["id"] for x in search(client, {"topic_id": str(hinh.id), "limit": 100}).json()["data"]})
    # several nodes: the union of their subtrees; a parent and its child do not double count
    both = search(client, {"topic_ids": [str(dai_so.id), str(hinh.id)], "limit": 100}).json()
    solo = lambda t: search(client, {"topic_id": str(t.id), "limit": 1}).json()["total"]  # noqa: E731
    assert both["total"] == solo(dai_so) + solo(hinh)
    leaf = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Tìm đỉnh và trục đối xứng parabol"))
    assert search(client, {"topic_ids": [str(dai_so.id), str(leaf.id)], "limit": 1}).json()["total"] == solo(dai_so)
    assert search(client, {"topic_ids": ["nope"]}).status_code == 422
    assert search(client, {"topic_ids": [str(uuid.uuid4())]}).json()["code"] == "validation_error"
    assert client.get("/api/questions").status_code == 405  # the list moved to POST /questions/search
    assert search(client, {"type": "true_false"}).json()["total"] == 0
    assert search(client, {"status": "needs_review"}).json()["total"] <= 6
    assert search(client, {"document_id": doc, "status": "all", "limit": 100}).json()["total"] == 40


def test_tag_filter_create_delete_restore(client, db):
    loaded(client, db)
    tag = client.post("/api/tags", json={"group": "skill", "name": "casio"}).json()
    body = {"type": "mcq", "stem": "Câu tạo tay ![](asset:11111111-1111-1111-1111-111111111111)", "options": OPTS,
            "answer": {"key": "C"}, "solution": "Vì vậy", "difficulty": "vd", "tag_ids": [tag["id"]]}
    r = client.post("/api/questions", json=body)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["status"] == "approved" and created["tags"][0]["name"] == "casio"
    assert [x["id"] for x in search(client, {"tag_ids": [tag["id"]]}).json()["data"]] == [created["id"]]
    assert client.post("/api/questions", json={**body, "answer": None}).status_code == 422
    assert client.delete(f"/api/questions/{created['id']}").status_code == 204
    assert client.get(f"/api/questions/{created['id']}").status_code == 404
    some = search(client).json()["data"][0]["id"]
    client.post("/api/questions/bulk", json={"ids": [some], "set": {"status": "rejected"}})
    rejected = search(client, {"status": "rejected"}).json()["data"]
    assert [x["id"] for x in rejected] == [some]
    assert client.post(f"/api/review/questions/{some}/action", json={"action": "restore"}).json()["status"] in ("auto_approved", "needs_review")


def test_bulk_difficulty_topic_tags(client, db):
    admin, _ = loaded(client, db)
    ids = [x["id"] for x in search(client, {"limit": 3}).json()["data"]]
    topic = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Vectơ"))
    tag = client.post("/api/tags", json={"group": "source", "name": "Đề 2025"}).json()
    r = client.post("/api/questions/bulk", json={"ids": ids, "set": {"difficulty": "vd", "primary_topic_id": str(topic.id), "add_tag_ids": [tag["id"]]}})
    assert r.json()["updated"] == 3
    for qid in ids:
        q = client.get(f"/api/questions/{qid}").json()
        assert q["difficulty"] == "vd" and q["topics"][0]["name"] == "Vectơ" and "Đề 2025" in [t["name"] for t in q["tags"]]
    assert client.post("/api/questions/bulk", json={"ids": ids + [str(uuid.uuid4())], "set": {"difficulty": "nb"}}).status_code == 404


def test_a_level_a_person_sets_is_marked_as_theirs_and_survives_the_machine(client, db):
    """difficulty-at-upload AC-04 over HTTP: whichever way a teacher sets a mức độ — the form, the bulk bar — the
    question records that a person set it, an invalid level is refused on every one of those ways, and an undo puts
    back the level the pipeline had put there rather than turning it into the teacher's own."""
    loaded(client, db)
    body = {"type": "mcq", "stem": "Đạo hàm của x^2", "options": OPTS, "answer": {"key": "C"}, "difficulty": "th"}
    made = client.post("/api/questions", json=body).json()
    assert (made["difficulty"], made["difficulty_source"]) == ("th", "manual")
    assert client.post("/api/questions", json={**body, "difficulty": "kho"}).status_code == 422

    qid = search(client, {"limit": 1}).json()["data"][0]["id"]
    # a level the pipeline wrote, as UOW-02 writes it: the trace is what tells it apart from a teacher's own
    db.execute(text("update questions set difficulty = 'nb', difficulty_source = 'auto' where id = :q"), {"q": qid})
    db.commit()
    assert client.get(f"/api/questions/{qid}").json()["difficulty_source"] == "auto"
    # PATCH used to store any string as a level: the check runs on this path too now
    bad = client.patch(f"/api/questions/{qid}", json={"difficulty": "trung bình"})
    assert bad.status_code == 422 and bad.json()["details"]["fields"]["difficulty"] == "Mức độ không hợp lệ"
    assert client.get(f"/api/questions/{qid}").json()["difficulty"] == "nb"
    patched = client.patch(f"/api/questions/{qid}", json={"difficulty": "vd"}).json()
    assert (patched["difficulty"], patched["difficulty_source"]) == ("vd", "manual")
    cleared = client.patch(f"/api/questions/{qid}", json={"difficulty": ""}).json()
    assert (cleared["difficulty"], cleared["difficulty_source"]) == (None, None)

    assert client.post("/api/questions/bulk", json={"ids": [qid], "set": {"difficulty": "kho"}}).status_code == 422
    db.execute(text("update questions set difficulty = 'nb', difficulty_source = 'auto' where id = :q"), {"q": qid})
    db.commit()
    assert client.post("/api/questions/bulk", json={"ids": [qid], "set": {"difficulty": "vdc"}}).json()["updated"] == 1
    assert client.get(f"/api/questions/{qid}").json()["difficulty_source"] == "manual"
    batch = client.post("/api/question-events/search", json={"limit": 1}).json()["data"][0]
    assert batch["fields"] == ["difficulty"]  # the trace moved with the level; it is not a second edit to show
    assert client.post("/api/questions/bulk/undo", json={"batch_id": batch["batch_id"]}).json()["restored"] == 1
    back = client.get(f"/api/questions/{qid}").json()
    assert (back["difficulty"], back["difficulty_source"]) == ("nb", "auto")


def test_one_bulk_request_writes_one_batch_carrying_the_whole_state(client, db):
    """ADR-01: the events of one request share a batch id — that is what makes a bulk edit one unit to read back
    and to take back. A-02: the recorded state covers every field the bar can move, topics and tags included."""
    admin, _ = loaded(client, db)
    ids = [x["id"] for x in search(client, {"limit": 2}).json()["data"]]
    topic = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Vectơ"))
    tag = client.post("/api/tags", json={"group": "source", "name": "Đề 2024"}).json()
    body = {"ids": ids, "set": {"difficulty": "th", "primary_topic_id": str(topic.id), "add_tag_ids": [tag["id"]]}}
    assert client.post("/api/questions/bulk", json=body).json()["updated"] == 2
    events = db.scalars(select(ReviewEvent).where(ReviewEvent.question_id.in_([uuid.UUID(i) for i in ids]),
                                                  ReviewEvent.action.in_(("bulk", "topic", "tag")))).all()
    assert len(events) == 6 and len({e.batch_id for e in events}) == 1 and events[0].batch_id is not None
    moved = next(e for e in events if e.action == "bulk")
    assert moved.before["difficulty"] != "th" and moved.after["difficulty"] == "th"
    assert moved.after["topics"] == [str(topic.id)] and moved.after["primary_topic"] == str(topic.id)
    assert tag["id"] in moved.after["tags"] and tag["id"] not in moved.before["tags"]
    assert set(moved.before) == set(moved.after) >= {"status", "answer", "confidence", "issues", "difficulty", "grade",
                                                     "subject_id", "topics", "primary_topic", "tags"}
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"difficulty": "vdc"}}).status_code == 200
    again = db.scalars(select(ReviewEvent).where(ReviewEvent.question_id.in_([uuid.UUID(i) for i in ids]),
                                                 ReviewEvent.action == "bulk")).all()
    assert len({e.batch_id for e in again}) == 2  # the second request is a batch of its own


def test_recent_changes_read_one_row_per_batch_and_say_why_one_cannot_be_undone(client, db):
    """AC-03 / AC-05: one row per edit — when, who, which fields, how many questions — newest first, each saying
    whether it can still be taken back. The `undo` rows are written here by hand: the command itself is UOW-02."""
    admin, _ = loaded(client, db)
    org = admin.organization_id
    ids = [x["id"] for x in search(client, {"limit": 3}).json()["data"]]
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"difficulty": "vdc"}}).json()["updated"] == 3
    assert client.post("/api/questions/bulk", json={"ids": ids[:1], "set": {"status": "rejected"}}).json()["updated"] == 1

    def changes(body=None):
        r = client.post("/api/question-events/search", json=body if body is not None else {"limit": 50})
        assert r.status_code == 200, r.text
        return r.json()

    page = changes()
    assert page["page"] == 1 and page["limit"] == 50 and page["total"] == len(page["data"])
    latest, older = page["data"][0], page["data"][1]
    assert latest["action"] == "bulk" and latest["questions"] == 1 and latest["fields"] == ["status"]
    assert older["action"] == "bulk" and older["questions"] == 3 and older["fields"] == ["difficulty"]
    assert older["actor_name"] and older["undoable"] is True and older["reason"] is None and older["batch_id"]
    # an aged batch, a batch an undo has reversed, the undo itself, and a row written before batches existed
    db.execute(text("update review_events set created_at = now() - interval '8 days' where batch_id = :b"), {"b": older["batch_id"]})
    db.execute(text("""insert into review_events (id, organization_id, action, after, batch_id)
                       values (gen_random_uuid(), :o, 'undo', jsonb_build_object('undone_batch_id', cast(:b as text)), gen_random_uuid())"""),
               {"o": org, "b": latest["batch_id"]})
    db.execute(text("""insert into review_events (id, organization_id, question_id, action, before, after)
                       values (gen_random_uuid(), :o, :q, 'bulk', '{"status": "needs_review"}', '{"status": "approved"}')"""),
               {"o": org, "q": ids[2]})
    db.commit()
    page = changes()
    by_batch = {x["batch_id"]: x for x in page["data"]}
    assert by_batch[older["batch_id"]]["undoable"] is False and by_batch[older["batch_id"]]["reason"] == "expired"
    assert "7 ngày" in by_batch[older["batch_id"]]["message"]
    assert by_batch[latest["batch_id"]]["reason"] == "already_undone" and by_batch[latest["batch_id"]]["undoable"] is False
    undo = next(x for x in page["data"] if x["action"] == "undo")
    assert undo["reason"] == "is_undo" and undo["questions"] == 0 and undo["actor_name"] is None
    before_batches = by_batch[None]
    assert before_batches["reason"] == "no_batch" and before_batches["questions"] == 1 and before_batches["fields"] == ["status"]
    assert changes({"limit": 1})["total"] == page["total"] and len(changes({"limit": 1})["data"]) == 1
    assert changes({"filters": {"questions": {"operator": ">=", "value": 3}}})["total"] == 1
    assert client.post("/api/question-events/search", json={"filters": {"nope": {"value": "x"}}}).json()["code"] == "bad_filter"
    # org-scoped and staff-only, like the rest of the bank
    other = client.__class__(client.app)
    make_user(db, make_org(db, "orgc"), "gvc", role="teacher")
    student = client.__class__(client.app)
    make_user(db, admin.organization, "hs2", role="student")
    db.commit()
    other.post("/api/auth/login", json={"org_code": "orgc", "username": "gvc", "password": "Secret123!"})
    student.post("/api/auth/login", json={"org_code": "trungtama", "username": "hs2", "password": "Secret123!"})
    assert other.post("/api/question-events/search", json={}).json()["total"] == 0
    assert student.post("/api/question-events/search", json={}).status_code == 403


def test_undo_puts_a_bulk_edit_back_and_only_once(client, db):
    """AC-01, AC-02, AC-04, AC-05 end to end: the batch the bulk bar wrote goes back as one unit and as one new row
    of the history, a second undo is refused, an undo is not itself undone, an aged batch is read-only, and a batch
    that lost a question is refused whole."""
    admin, _ = loaded(client, db)
    was = {x["id"]: x for x in search(client, {"limit": 3}).json()["data"]}
    ids = list(was)
    topic = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Vectơ"))
    tag = client.post("/api/tags", json={"group": "source", "name": "Đề 2022"}).json()
    edit = {"status": "rejected", "difficulty": "vdc", "primary_topic_id": str(topic.id), "add_tag_ids": [tag["id"]]}
    edited = client.post("/api/questions/bulk", json={"ids": ids, "set": edit}).json()
    assert edited["updated"] == 3
    row = client.post("/api/question-events/search", json={"limit": 1}).json()["data"][0]
    assert row["questions"] == 3 and row["undoable"] is True
    # the edit names its own batch: the toast undoes what it just reported instead of guessing which row is its own
    assert edited["batch_id"] == row["batch_id"]

    r = client.post("/api/questions/bulk/undo", json={"batch_id": row["batch_id"]})
    assert r.status_code == 200, r.text
    assert r.json()["restored"] == 3 and r.json()["batch_id"] != row["batch_id"]
    for qid, before in was.items():
        now = client.get(f"/api/questions/{qid}").json()
        assert (now["status"], now["difficulty"], now["grade"], now["subject_id"]) == \
               (before["status"], before["difficulty"], before["grade"], before["subject_id"])
        assert [t["id"] for t in now["topics"]] == [t["id"] for t in before["topics"]]
        assert [t["id"] for t in now["tags"]] == [t["id"] for t in before["tags"]]

    # the undo is a row of its own, the batch it took back says so, and neither offers undo again (AC-04)
    rows = client.post("/api/question-events/search", json={"limit": 10}).json()["data"]
    undone, original = rows[0], next(x for x in rows if x["batch_id"] == row["batch_id"])
    assert undone["action"] == "undo" and undone["questions"] == 3 and undone["batch_id"] == r.json()["batch_id"]
    assert undone["undoable"] is False and undone["reason"] == "is_undo"
    assert original["undoable"] is False and original["reason"] == "already_undone"
    again = client.post("/api/questions/bulk/undo", json={"batch_id": row["batch_id"]})
    assert again.status_code == 409 and again.json()["code"] == "batch_already_undone"
    assert again.json()["details"]["fields"]["undone_by"] == undone["batch_id"]
    twice = client.post("/api/questions/bulk/undo", json={"batch_id": undone["batch_id"]})
    assert twice.status_code == 409 and twice.json()["code"] == "batch_is_undo"
    assert client.post("/api/questions/bulk/undo", json={"batch_id": str(uuid.uuid4())}).status_code == 404

    # a batch that moved neither the placement nor the tags leaves the links alone: the topic the pipeline placed
    # stays the pipeline's, with its score, instead of coming back as a teacher's own placement
    placed = next(x for x in search(client, {"limit": 20}).json()["data"] if x["topics"] and x["id"] not in ids)
    assert client.post("/api/questions/bulk", json={"ids": [placed["id"]], "set": {"difficulty": "nb"}}).json()["updated"] == 1
    solo = client.post("/api/question-events/search", json={"limit": 1}).json()["data"][0]["batch_id"]
    assert client.post("/api/questions/bulk/undo", json={"batch_id": solo}).json()["restored"] == 1
    assert client.get(f"/api/questions/{placed['id']}").json()["topics"] == placed["topics"]

    # past the window it is still readable and no longer undoable (AC-05)
    assert client.post("/api/questions/bulk", json={"ids": ids[:1], "set": {"difficulty": "th"}}).json()["updated"] == 1
    aged = client.post("/api/question-events/search", json={"limit": 1}).json()["data"][0]["batch_id"]
    db.execute(text("update review_events set created_at = now() - interval '8 days' where batch_id = :b"), {"b": aged})
    db.commit()
    expired = client.post("/api/questions/bulk/undo", json={"batch_id": aged})
    assert expired.status_code == 422 and expired.json()["code"] == "batch_expired"
    assert expired.json()["details"]["fields"]["age_days"] == 8 and "7 ngày" in expired.json()["message"]
    assert client.get(f"/api/questions/{ids[0]}").json()["difficulty"] == "th"

    # a question the batch touched is deleted: the whole batch is refused, nothing else is put back (AC-02)
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"difficulty": "nb"}}).json()["updated"] == 3
    last = client.post("/api/question-events/search", json={"limit": 1}).json()["data"][0]["batch_id"]
    assert client.delete(f"/api/questions/{ids[2]}").status_code == 204
    gone = client.post("/api/questions/bulk/undo", json={"batch_id": last})
    assert gone.status_code == 422 and gone.json()["code"] == "questions_gone", gone.text
    assert client.get(f"/api/questions/{ids[0]}").json()["difficulty"] == "nb"
    # the deletion left the history alone, so the refusal can say which question it could not put back
    # (history-keeps-ids AC-01, AC-03)
    assert gone.json()["details"]["fields"]["question_ids"] == [ids[2]]
    kept = db.execute(text("select count(*) from review_events where question_id = :q"), {"q": ids[2]}).scalar()
    assert kept and not db.execute(text("select count(*) from questions where id = :q"), {"q": ids[2]}).scalar()

    # org-scoped and staff-only, like the rest of the bank
    other = client.__class__(client.app)
    make_user(db, make_org(db, "orgd"), "gvd", role="teacher")
    student = client.__class__(client.app)
    make_user(db, admin.organization, "hs3", role="student")
    db.commit()
    other.post("/api/auth/login", json={"org_code": "orgd", "username": "gvd", "password": "Secret123!"})
    student.post("/api/auth/login", json={"org_code": "trungtama", "username": "hs3", "password": "Secret123!"})
    assert other.post("/api/questions/bulk/undo", json={"batch_id": last}).status_code == 404
    assert student.post("/api/questions/bulk/undo", json={"batch_id": last}).status_code == 403


def test_permissions_and_isolation(client, db):
    admin, _ = loaded(client, db)
    student = client.__class__(client.app)
    make_user(db, admin.organization, "hs", role="student")
    other = client.__class__(client.app)
    make_user(db, make_org(db, "orgb"), "gvb", role="teacher")
    db.commit()
    student.post("/api/auth/login", json={"org_code": "trungtama", "username": "hs", "password": "Secret123!"})
    other.post("/api/auth/login", json={"org_code": "orgb", "username": "gvb", "password": "Secret123!"})
    assert search(student).status_code == 403
    assert search(other).json()["total"] == 0
    qid = search(client).json()["data"][0]["id"]
    assert other.patch(f"/api/questions/{qid}", json={"stem": "x"}).status_code == 404
    assert other.delete(f"/api/questions/{qid}").status_code == 404


def test_search_10k_under_300ms(client, db):
    admin = setup_admin(client, db)
    db.execute(text("""
        insert into questions (id, organization_id, type, stem, options, solution, status, search_text, issues, spot_check)
        select gen_random_uuid(), :o, 'mcq', 'Câu số ' || g || ' về parabol và vectơ', '[]', '', 'approved',
               'causo' || g || 'veparabolvavecto' || md5(g::text), '[]', false
          from generate_series(1, 10000) g"""), {"o": admin.organization_id})
    db.commit()
    db.execute(text("analyze questions"))
    search(client, {"q": "parabol"})  # warm up
    t = time.perf_counter()
    r = search(client, {"q": "parabol", "grade": 10})
    assert r.status_code == 200
    t2 = time.perf_counter()
    r = search(client, {"q": "vecto parabol"})
    assert (time.perf_counter() - t2) < 0.3 and (t2 - t) < 0.3, (t2 - t, time.perf_counter() - t2)


def test_bulk_sets_subject_and_grade_and_refuses_a_topic_of_another_subject(client, db):
    """pickers-builder AC-05: the "Chưa phân môn" tab becomes actionable. A-04: a new subject never silently
    leaves a question in another subject's tree — the whole edit is refused, naming what is in the way."""
    from app.modules.taxonomy.domain.entities import Subject

    admin, _ = loaded(client, db)
    org = admin.organization_id
    toan = db.scalar(select(Subject).where(Subject.organization_id == org, Subject.code == "toan"))
    ly = db.scalar(select(Subject).where(Subject.organization_id == org, Subject.code == "ly"))
    unclassified = search(client, {"subject_id": "none", "status": "all", "limit": 3}).json()
    ids = [q["id"] for q in unclassified["data"]]
    assert len(ids) == 3 and unclassified["total"] > 3
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"subject_id": str(toan.id), "grade": 11}}).json()["updated"] == 3
    one = client.get(f"/api/questions/{ids[0]}").json()
    assert one["subject_id"] == str(toan.id) and one["grade"] == 11
    assert search(client, {"subject_id": "none", "status": "all", "limit": 1}).json()["total"] == unclassified["total"] - 3
    bad = client.post("/api/questions/bulk", json={"ids": ids, "set": {"grade": 13}})
    assert bad.status_code == 422 and bad.json()["details"]["fields"] == {"grade": "Lớp không hợp lệ"}
    assert client.post("/api/questions/bulk", json={"ids": ids, "set": {"subject_id": str(uuid.uuid4())}}).status_code == 422
    topic = client.post("/api/topics", json={"name": "Dao động điều hòa", "subject_id": str(ly.id), "level_kind": "topic"}).json()
    assert client.patch(f"/api/questions/{ids[0]}", json={"primary_topic_id": topic["id"]}).status_code == 200
    r = client.post("/api/questions/bulk", json={"ids": ids, "set": {"subject_id": str(toan.id), "grade": 12}})
    assert r.status_code == 422 and r.json()["code"] == "subject_topic_conflict"
    assert r.json()["details"]["fields"]["conflicts"] == [{"question_id": ids[0], "topic_id": topic["id"], "topic_name": "Dao động điều hòa"}]
    assert "Dao động điều hòa" in r.json()["message"]
    assert client.get(f"/api/questions/{ids[1]}").json()["grade"] == 11  # nothing was applied
