from sqlalchemy import select

from app.models import StudentTopicMastery
from app.services import mastery
from tests.exam_helpers import assign, display_key, display_wrong, exam_with_questions, klass_with_student, login


def test_step_is_difficulty_weighted_ema():
    assert mastery.step(0.5, 1.0, "th") == 0.65
    assert mastery.step(0.5, 1.0, "vdc") == round(0.5 + 0.42 * 0.5, 6)
    assert mastery.step(0.5, 0.0, "nb") == round(0.5 - 0.24 * 0.5, 6)
    assert mastery.step(0.5, 1.0, None) == 0.65


def take(client, db, right: bool, username="hs01"):
    admin, exam = exam_with_questions(client, db, mcq=4, tf=0, short=0)
    klass, _ = klass_with_student(client, db, admin, username)
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", username)
    att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
    for q in s.get(f"/api/attempts/{att}").json()["questions"]:
        s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q) if right else display_wrong(db, q)})
    s.post(f"/api/attempts/{att}/submit")
    return admin


def test_grading_updates_mastery_and_backfill_matches(client, db):
    admin = take(client, db, right=True)
    rows = db.scalars(select(StudentTopicMastery)).all()
    assert rows and all(r.mastery > 0.5 and r.answers >= 1 for r in rows)
    before = {(r.student_id, r.topic_id): (round(r.mastery, 6), r.answers) for r in rows}
    assert mastery.backfill(db, admin.organization_id) >= 4
    db.commit()
    after = {(r.student_id, r.topic_id): (round(r.mastery, 6), r.answers) for r in db.scalars(select(StudentTopicMastery))}
    assert after == before


def test_wrong_answers_lower_mastery(client, db):
    take(client, db, right=False)
    assert all(r.mastery < 0.5 for r in db.scalars(select(StudentTopicMastery)))
