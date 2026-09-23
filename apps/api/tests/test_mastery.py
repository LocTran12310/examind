from sqlalchemy import delete, select

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.services import mastery
from app.modules.analytics.interface.deps import analytics_api
from tests.exam_helpers import assign, display_key, display_wrong, exam_with_questions, klass_with_student, login

ENOUGH = mastery.MIN_ANSWERS  # rounds of the same exam: one answer per question each, so every topic passes the minimum


def test_step_is_difficulty_weighted_ema():
    assert mastery.step(0.5, 1.0, "th") == 0.65
    assert mastery.step(0.5, 1.0, "vdc") == round(0.5 + 0.42 * 0.5, 6)
    assert mastery.step(0.5, 0.0, "nb") == round(0.5 - 0.24 * 0.5, 6)
    assert mastery.step(0.5, 1.0, None) == 0.65


def take(client, db, right: bool, username="hs01", rounds=1):
    """`rounds` sittings of the same 4-question exam; one round leaves every topic under the weak rule's minimum."""
    admin, exam = exam_with_questions(client, db, mcq=4, tf=0, short=0)
    klass, _ = klass_with_student(client, db, admin, username)
    s = login(client, "trungtama", username)
    for _ in range(rounds):
        a = assign(client, exam["id"], klass["id"])
        att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
        for q in s.get(f"/api/attempts/{att}").json()["questions"]:
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q) if right else display_wrong(db, q)})
        s.post(f"/api/attempts/{att}/submit")
    return admin


def test_grading_updates_mastery_and_backfill_matches(client, db):
    admin = take(client, db, right=True)
    rows = db.scalars(select(TopicMastery)).all()
    assert rows and all(r.mastery > 0.5 and r.answers >= 1 for r in rows)
    before = {(r.student_id, r.topic_id): (round(r.mastery, 6), r.answers) for r in rows}
    assert analytics_api(db).rebuild_mastery(admin.organization_id) >= 4
    db.commit()
    after = {(r.student_id, r.topic_id): (round(r.mastery, 6), r.answers) for r in db.scalars(select(TopicMastery))}
    assert after == before


def test_wrong_answers_lower_mastery(client, db):
    take(client, db, right=False)
    assert all(r.mastery < 0.5 for r in db.scalars(select(TopicMastery)))


def test_bootstrap_backfills_when_table_is_empty(client, db):
    from app.seed.bootstrap import backfill_mastery_if_missing

    take(client, db, right=True)
    db.execute(delete(TopicMastery))
    db.commit()
    assert backfill_mastery_if_missing(db) >= 4
    db.commit()
    assert db.scalars(select(TopicMastery)).first() is not None
    assert backfill_mastery_if_missing(db) == 0
