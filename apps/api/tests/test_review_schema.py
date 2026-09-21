from sqlalchemy import text

from app.models import Question, ReviewEvent
from tests.factories import make_org


def test_trigram_and_review_events(db):
    org = make_org(db)
    q = Question(organization_id=org.id, stem="Tọa độ đỉnh parabol", search_text="toa do dinh parabol", status="needs_review")
    db.add(q)
    db.flush()
    db.add(ReviewEvent(organization_id=org.id, question_id=q.id, action="approve", before={"status": "needs_review"}, after={"status": "approved"}))
    db.commit()
    sim = db.execute(text("select similarity(search_text, 'toa do dinh cua parabol') from questions where id=:i"), {"i": q.id}).scalar()
    assert sim > 0.6
    assert db.execute(text("select unaccent('Tọa độ đỉnh')")).scalar() == "Toa do dinh"
    bad = Question(organization_id=org.id, stem="x", status="weird")
    db.add(bad)
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
