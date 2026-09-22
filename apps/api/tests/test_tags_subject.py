"""Tags by subject (subject-scoped-bank AC-06, AC-07)."""
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.models import Question, QuestionTag, Subject, Tag
from tests.conftest import HERE, TEST_URL
from tests.test_review_api import setup_admin


def subjects(db, org_id):
    return {s.code: s for s in db.scalars(select(Subject).where(Subject.organization_id == org_id))}


def test_tags_of_a_subject_plus_shared(client, db):
    admin = setup_admin(client, db)
    s = subjects(db, admin.organization_id)
    toan, ly = s["toan"], s["ly"]
    t1 = client.post("/api/tags", json={"group": "method", "name": "Đổi biến", "subject_id": str(toan.id)}).json()
    t2 = client.post("/api/tags", json={"group": "custom", "name": "Có hình vẽ"}).json()
    src = client.post("/api/tags", json={"group": "source", "name": "Sở GD&ĐT Ninh Bình", "subject_id": str(toan.id)}).json()
    assert t1["subject_id"] == str(toan.id) and t2["subject_id"] is None
    assert src["subject_id"] is None  # nguồn đề stays shared
    names = lambda **p: {t["name"] for t in client.get("/api/tags", params={"page_size": "all", **p}).json()["items"]}  # noqa: E731
    assert names(subject_id=str(toan.id)) == {"Đổi biến", "Có hình vẽ", "Sở GD&ĐT Ninh Bình"}
    assert names(subject_id=str(ly.id)) == {"Có hình vẽ", "Sở GD&ĐT Ninh Bình"}
    assert names(subject_id=str(toan.id), include_shared="false") == {"Đổi biến"}
    assert names(subject_id="shared") == {"Có hình vẽ", "Sở GD&ĐT Ninh Bình"}
    # move to another subject, then make it shared
    assert client.patch(f"/api/tags/{t1['id']}", json={"subject_id": str(ly.id)}).json()["subject_id"] == str(ly.id)
    assert client.patch(f"/api/tags/{t1['id']}", json={"name": "Đổi biến số"}).json()["subject_id"] == str(ly.id)
    assert client.patch(f"/api/tags/{t1['id']}", json={"subject_id": None}).json()["subject_id"] is None
    assert client.post("/api/tags", json={"name": "x", "subject_id": "00000000-0000-0000-0000-000000000000"}).status_code == 422


def test_backfill_gives_single_subject_tags_their_subject(client, db):
    admin = setup_admin(client, db)
    s = subjects(db, admin.organization_id)
    org = admin.organization_id
    only_toan, mixed, source = (Tag(organization_id=org, group=g, name=n) for g, n in (("method", "Toán thôi"), ("custom", "Trộn"), ("source", "Nguồn")))
    db.add_all([only_toan, mixed, source])
    q1 = Question(organization_id=org, subject_id=s["toan"].id, stem="a", status="approved")
    q2 = Question(organization_id=org, subject_id=s["ly"].id, stem="b", status="approved")
    db.add_all([q1, q2])
    db.flush()
    db.add_all([QuestionTag(question_id=q1.id, tag_id=only_toan.id), QuestionTag(question_id=q1.id, tag_id=mixed.id),
                QuestionTag(question_id=q2.id, tag_id=mixed.id), QuestionTag(question_id=q1.id, tag_id=source.id)])
    db.commit()
    cfg = Config(os.path.join(HERE, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(HERE, "migrations"))
    cfg.attributes["url"] = TEST_URL
    command.downgrade(cfg, "0015")
    command.upgrade(cfg, "head")
    db.expire_all()
    got = {t.name: t.subject_id for t in db.scalars(select(Tag).where(Tag.organization_id == org))}
    assert got == {"Toán thôi": s["toan"].id, "Trộn": None, "Nguồn": None}
