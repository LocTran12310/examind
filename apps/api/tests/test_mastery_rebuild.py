from sqlalchemy import select

from app.modules.analytics.domain.entities import TopicMastery
from tests.exam_helpers import login
from tests.factories import make_org, make_user
from tests.test_mastery import ENOUGH, take


def kept(db) -> dict:
    db.expire_all()
    return {(r.student_id, r.topic_id): (round(r.mastery, 6), r.answers) for r in db.scalars(select(TopicMastery))}


def test_an_org_admin_replays_the_facts_onto_the_same_numbers(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    before = kept(db)
    r = client.post("/api/analytics/mastery/rebuild")
    assert r.status_code == 200, r.text
    assert r.json() == {"students": 1, "topics": len(before), "facts": 4 * ENOUGH}
    assert kept(db) == before  # decay is part of the rules, so the replay lands where live grading did


def test_the_replay_leaves_another_organisation_alone(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    other = make_org(db, code="trungtamb", name="Trung tâm B")
    stranger = make_user(db, other, "hs99", role="student")
    db.add(TopicMastery(student_id=stranger.id, topic_id=db.scalar(select(TopicMastery.topic_id)), organization_id=other.id,
                        mastery=0.1, answers=9))
    db.commit()
    before = kept(db)
    assert client.post("/api/analytics/mastery/rebuild").json()["students"] == 1  # only the admin's own students
    assert kept(db) == before


def test_teachers_and_students_may_not_rebuild(client, db):
    admin = take(client, db, right=False, rounds=ENOUGH)
    make_user(db, admin.organization, "gv01", role="teacher")
    db.commit()
    for username in ("gv01", "hs01"):
        assert login(client, "trungtama", username).post("/api/analytics/mastery/rebuild").status_code == 403
