"""Bank by subject: 'none' subject, school year, tag groups, facet counts (subject-scoped-bank AC-03, AC-05, AC-09)."""
import uuid

from sqlalchemy import select

from app.modules.bank.domain.entities import Question, QuestionTag, QuestionTopic

from app.modules.ingestion.domain.entities import SourceDocument

from app.modules.taxonomy.domain.entities import Subject, Tag

from app.modules.taxonomy.domain.topics import Topic
from app.modules.taxonomy.domain.topics import topic_label
from tests.test_review_api import setup_admin


def build(db, org):
    s = {x.code: x for x in db.scalars(select(Subject).where(Subject.organization_id == org))}
    toan, ly = s["toan"], s["ly"]

    def topic(name, parent=None, subject=toan):
        tid = uuid.uuid4()
        path = (parent.path + "." if parent else "") + topic_label(tid)
        t = Topic(id=tid, organization_id=org, subject_id=subject.id, parent_id=parent and parent.id, name=name, level_kind="topic", path=path)
        db.add(t)
        return t

    ham_so = topic("Hàm số X")
    don_dieu = topic("Đơn điệu X", ham_so)
    tich_phan = topic("Tích phân X")
    dong_dien = topic("Dòng điện X", subject=ly)
    docs = {y: SourceDocument(organization_id=org, filename=f"{y}.docx", mime="x", size=1, file_hash=y, storage_key=y, meta={"school_year": y})
            for y in ("2023-2024", "2024-2025")}
    db.add_all(docs.values())
    nb = Tag(organization_id=org, group="source", name="Sở Ninh Bình")
    hinh = Tag(organization_id=org, group="custom", name="Có hình")
    db.add_all([nb, hinh])
    db.flush()

    def q(subject, topic_=None, kind="mcq", exam_kind="Thi thử", year="2024-2025", tags=()):
        x = Question(organization_id=org, subject_id=subject and subject.id, type=kind, stem="s", status="approved",
                     exam_kind=exam_kind, source_document_id=docs[year].id if year else None)
        db.add(x)
        db.flush()
        if topic_:
            db.add(QuestionTopic(question_id=x.id, topic_id=topic_.id, is_primary=True))
        for t in tags:
            db.add(QuestionTag(question_id=x.id, tag_id=t.id))
        return x

    q(toan, don_dieu, tags=(nb, hinh))
    q(toan, don_dieu, kind="true_false", tags=(nb,))
    q(toan, ham_so, exam_kind="Giữa kỳ", year="2023-2024", tags=(hinh,))
    q(toan, tich_phan, kind="short_answer", tags=(nb,))
    q(ly, dong_dien, tags=(nb,))
    q(None, None, year=None)
    db.commit()
    return dict(toan=toan, ly=ly, ham_so=ham_so, don_dieu=don_dieu, tich_phan=tich_phan, dong_dien=dong_dien, nb=nb, hinh=hinh)


def total(client, **p):
    return client.post("/api/questions/search", json={"limit": 1, **p}).json()["total"]


def test_filters_by_none_subject_year_and_tag_groups(client, db):
    admin = setup_admin(client, db)
    x = build(db, admin.organization_id)
    assert total(client, subject_id="none") == 1
    assert total(client, subject_id=str(x["toan"].id), school_year="2024-2025") == 3
    # same group: any; different groups: all
    assert total(client, subject_id=str(x["toan"].id), tag_ids=[str(x["nb"].id), str(x["hinh"].id)]) == 1
    assert total(client, tag_ids=[str(x["nb"].id)]) == 4
    assert client.post("/api/questions/search", json={"subject_id": "toán"}).status_code == 422


def test_facets_exclude_their_own_dimension(client, db):
    admin = setup_admin(client, db)
    x = build(db, admin.organization_id)
    toan = str(x["toan"].id)
    f = client.post("/api/questions/facets", json={"subject_id": toan, "exam_kind": "Thi thử"}).json()
    assert f["subjects"] == {toan: 3, str(x["ly"].id): 1, "none": 1}  # other subjects visible, with the other filters
    assert f["types"] == {"mcq": 1, "true_false": 1, "short_answer": 1}
    assert f["periods"] == {"|Thi thử": 3, "|Giữa kỳ": 1}  # own dimension ignored
    assert f["school_years"] == {"2024-2025": 3}
    assert f["topics"] == {str(x["ham_so"].id): 2, str(x["don_dieu"].id): 2, str(x["tich_phan"].id): 1}  # subtree totals, Toán only
    assert f["tags"] == {str(x["nb"].id): 3, str(x["hinh"].id): 1}
    f = client.post("/api/questions/facets", json={"subject_id": toan, "topic_ids": [str(x["don_dieu"].id)]}).json()
    assert f["topics"][str(x["ham_so"].id)] == 3 and f["types"] == {"mcq": 1, "true_false": 1}
