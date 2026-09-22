import time
import uuid

from sqlalchemy import select, text

from app.models import Question, Topic
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
    assert r.json() == {"updated": 3}
    for qid in ids:
        q = client.get(f"/api/questions/{qid}").json()
        assert q["difficulty"] == "vd" and q["topics"][0]["name"] == "Vectơ" and "Đề 2025" in [t["name"] for t in q["tags"]]
    assert client.post("/api/questions/bulk", json={"ids": ids + [str(uuid.uuid4())], "set": {"difficulty": "nb"}}).status_code == 404


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
