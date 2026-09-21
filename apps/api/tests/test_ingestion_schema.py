import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Question, QuestionTopic, SourceDocument, Topic
from app.seed.org_template import seed_org
from tests.factories import make_org


def test_document_hash_unique_per_org(db):
    a, b = make_org(db, "orga"), make_org(db, "orgb")
    for org in (a, b):
        db.add(SourceDocument(organization_id=org.id, filename="x.docx", mime="m", size=1, file_hash="h" * 64, storage_key="k"))
    db.commit()
    db.add(SourceDocument(organization_id=a.id, filename="y.docx", mime="m", size=1, file_hash="h" * 64, storage_key="k2"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_one_primary_topic_per_question(db):
    org = make_org(db)
    seed_org(db, org.id)
    t1, t2 = db.query(Topic).filter_by(organization_id=org.id).limit(2).all()
    q = Question(organization_id=org.id, stem="x", issues=["thiếu đáp án"], confidence=0.5, number=3, part="I")
    db.add(q)
    db.flush()
    db.add(QuestionTopic(question_id=q.id, topic_id=t1.id, is_primary=True, source="auto", score=0.8))
    db.add(QuestionTopic(question_id=q.id, topic_id=t2.id, is_primary=False))
    db.commit()
    db.add(QuestionTopic(question_id=q.id, topic_id=t2.id, is_primary=True))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
