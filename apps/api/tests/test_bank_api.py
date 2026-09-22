import time
import uuid

from sqlalchemy import select, text

from app.models import Question, Topic
from tests.factories import make_org, make_user
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin

OPTS = [{"label": l, "content": c} for l, c in zip("ABCD", ["1", "2", "3", "4"])]


def loaded(client, db):
    admin = setup_admin(client, db)
    doc = upload(client, "m.docx", sample("de-mau-toan10.docx"), meta={"grade": 10}).json()["document"]["id"]
    run_jobs()
    return admin, doc


def test_search_text_filters_and_topic_subtree(client, db):
    admin, doc = loaded(client, db)
    r = client.get("/api/questions", params={"q": "parabol"}).json()
    assert r["total"] >= 5 and all("parabol" in x["stem"] for x in r["items"])
    r = client.get("/api/questions", params={"q": "tọa độ đỉnh", "grade": 10}).json()
    assert r["total"] >= 5
    dai_so = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Đại số"))
    leafs = client.get("/api/questions", params={"topic_id": str(dai_so.id), "page_size": 100}).json()
    names = {x["topics"][0]["name"] for x in leafs["items"]}
    assert "Tìm đỉnh và trục đối xứng parabol" in names and leafs["total"] >= 10
    hinh = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Hình học"))
    assert not ({x["id"] for x in leafs["items"]} & {x["id"] for x in client.get("/api/questions", params={"topic_id": str(hinh.id), "page_size": 100}).json()["items"]})
    # several nodes: the union of their subtrees; a parent and its child do not double count
    both = client.get("/api/questions", params={"topic_ids": f"{dai_so.id},{hinh.id}", "page_size": 100}).json()
    solo = lambda t: client.get("/api/questions", params={"topic_id": str(t.id), "page_size": 1}).json()["total"]  # noqa: E731
    assert both["total"] == solo(dai_so) + solo(hinh)
    leaf = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Tìm đỉnh và trục đối xứng parabol"))
    assert client.get("/api/questions", params={"topic_ids": f"{dai_so.id},{leaf.id}", "page_size": 1}).json()["total"] == solo(dai_so)
    assert client.get("/api/questions", params={"topic_ids": "nope"}).status_code == 422
    assert client.get("/api/questions", params={"type": "true_false"}).json()["total"] == 0
    assert client.get("/api/questions", params={"status": "needs_review"}).json()["total"] <= 6
    assert client.get("/api/questions", params={"document_id": doc, "status": "all", "page_size": 100}).json()["total"] == 40


def test_tag_filter_create_delete_restore(client, db):
    loaded(client, db)
    tag = client.post("/api/tags", json={"group": "skill", "name": "casio"}).json()
    body = {"type": "mcq", "stem": "Câu tạo tay ![](asset:11111111-1111-1111-1111-111111111111)", "options": OPTS,
            "answer": {"key": "C"}, "solution": "Vì vậy", "difficulty": "vd", "tag_ids": [tag["id"]]}
    r = client.post("/api/questions", json=body)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["status"] == "approved" and created["tags"][0]["name"] == "casio"
    assert [x["id"] for x in client.get("/api/questions", params={"tag_ids": [tag["id"]]}).json()["items"]] == [created["id"]]
    assert client.post("/api/questions", json={**body, "answer": None}).status_code == 422
    assert client.delete(f"/api/questions/{created['id']}").status_code == 204
    assert client.get(f"/api/questions/{created['id']}").status_code == 404
    some = client.get("/api/questions").json()["items"][0]["id"]
    client.post("/api/questions/bulk", json={"ids": [some], "set": {"status": "rejected"}})
    rejected = client.get("/api/questions", params={"status": "rejected"}).json()["items"]
    assert [x["id"] for x in rejected] == [some]
    assert client.post(f"/api/review/questions/{some}/action", json={"action": "restore"}).json()["status"] in ("auto_approved", "needs_review")


def test_bulk_difficulty_topic_tags(client, db):
    admin, _ = loaded(client, db)
    ids = [x["id"] for x in client.get("/api/questions", params={"page_size": 3}).json()["items"]]
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
    assert student.get("/api/questions").status_code == 403
    assert other.get("/api/questions").json()["total"] == 0
    qid = client.get("/api/questions").json()["items"][0]["id"]
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
    client.get("/api/questions", params={"q": "parabol"})  # warm up
    t = time.perf_counter()
    r = client.get("/api/questions", params={"q": "parabol", "grade": 10})
    assert r.status_code == 200
    t2 = time.perf_counter()
    r = client.get("/api/questions", params={"q": "vecto parabol"})
    assert (time.perf_counter() - t2) < 0.3 and (t2 - t) < 0.3, (t2 - t, time.perf_counter() - t2)
