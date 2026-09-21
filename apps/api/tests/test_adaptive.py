from datetime import timedelta
import time

from sqlalchemy import select, text

from app.core.security import now
from app.models import AnswerFact, Question, QuestionTopic, StudentTopicMastery, Topic, User
from app.services import adaptive
from tests.test_mastery import take


def setup(client, db):
    admin = take(client, db, right=False)  # hs01 answered 4 MCQs wrong → weak topics
    student = db.scalar(select(User).where(User.username == "hs01"))
    return admin, student


def test_no_history_gives_balanced_exam(client, db):
    from tests.test_exams_api import bank_ready

    admin, _ = bank_ready(client, db)
    from tests.factories import make_user

    s = make_user(db, admin.organization, "moi", role="student")
    db.commit()
    plan = adaptive.build_plan(db, admin.organization_id, s.id, count=10, seed=1)
    assert len(plan.picks) == 10 and "Chưa có dữ liệu" in plan.note
    assert len({p.question_id for p in plan.picks}) == 10


def test_composition_targets_weak_topics_and_reasks_old_mistakes(client, db):
    admin, student = setup(client, db)
    # make the mistakes older than 24 h so they are due for a re-ask
    db.execute(text("update answer_facts set created_at = created_at - interval '2 days'"))
    db.commit()
    plan = adaptive.build_plan(db, admin.organization_id, student.id, count=20, seed=3)
    reasons = [p.reason for p in plan.picks]
    assert len(plan.picks) == 20 and len(plan.ids()) == 20
    assert reasons.count("Ôn lại câu từng làm sai") == 2
    weak_topics = [tp for m, tp in db.execute(select(StudentTopicMastery, Topic).join(Topic, Topic.id == StudentTopicMastery.topic_id)
                                                .where(StudentTopicMastery.student_id == student.id).order_by(StudentTopicMastery.mastery)).all()][:3]
    weak_paths = [t.path for t in weak_topics]
    parents = {t.path.rsplit(".", 1)[0] for t in weak_topics if "." in t.path}
    in_weak = 0
    for p in plan.picks:
        if p.reason != "Chuyên đề yếu":
            continue
        paths = db.scalars(select(Topic.path).join(QuestionTopic, QuestionTopic.topic_id == Topic.id).where(QuestionTopic.question_id == p.question_id)).all()
        in_weak += any(any(pp == w or pp.startswith(w + ".") for w in weak_paths + list(parents)) for pp in paths)
    assert in_weak >= 11  # ~60% of 20 from the weakest topics or their neighbours


def test_excludes_recent_correct_and_flagged(client, db):
    admin = take(client, db, right=True)
    student = db.scalar(select(User).where(User.username == "hs01"))
    recent = set(db.scalars(select(AnswerFact.question_id).where(AnswerFact.student_id == student.id)))
    flagged = db.scalars(select(Question).where(Question.organization_id == admin.organization_id, Question.id.notin_(recent)).limit(3)).all()
    for q in flagged:
        q.status = "flagged"
    db.commit()
    plan = adaptive.build_plan(db, admin.organization_id, student.id, count=20, seed=5)
    assert not (plan.ids() & recent) and not (plan.ids() & {q.id for q in flagged})


def test_difficulty_targets():
    assert adaptive.target_difficulties(0.2) == ["nb", "th"]
    assert adaptive.target_difficulties(0.55) == ["th", "vd"]
    assert adaptive.target_difficulties(0.9) == ["vd", "vdc"]


def test_generation_speed(client, db):
    admin, student = setup(client, db)
    leaf = db.scalar(select(Topic).where(Topic.organization_id == admin.organization_id, Topic.name == "Tìm đỉnh và trục đối xứng parabol"))
    db.execute(text("""insert into questions (id, organization_id, type, stem, options, solution, status, search_text, issues, spot_check)
                       select gen_random_uuid(), :o, 'mcq', 'q' || g, '[]', '', 'approved', 'q' || g, '[]', false from generate_series(1, 10000) g"""),
               {"o": admin.organization_id})
    db.execute(text("""insert into question_topics (question_id, topic_id, is_primary, source)
                       select id, :t, true, 'manual' from questions where stem like 'q%' and organization_id = :o"""),
               {"t": leaf.id, "o": admin.organization_id})
    db.execute(text("""insert into answer_facts (id, organization_id, attempt_id, exam_id, student_id, question_id, topic_path, tag_ids, qtype,
                                                 points, max_points, correct_ratio, created_at)
                       select gen_random_uuid(), :o, (select attempt_id from answer_facts limit 1), gen_random_uuid(), :s, gen_random_uuid(),
                              cast(:p as ltree), '{}', 'mcq', 0, 0.25, 0, now() - interval '3 days' from generate_series(1, 50000)"""),
               {"o": admin.organization_id, "s": student.id, "p": leaf.path})
    db.commit()
    db.execute(text("analyze"))
    t = time.perf_counter()
    plan = adaptive.build_plan(db, admin.organization_id, student.id, count=20, seed=1)
    assert len(plan.picks) == 20 and time.perf_counter() - t < 0.5, time.perf_counter() - t
