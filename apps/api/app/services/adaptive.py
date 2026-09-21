"""Personal review exams (adaptive-review US-02, US-03, A-03..A-07, ADR-02)."""
from dataclasses import dataclass, field
from datetime import timedelta
import random
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import now
from app.models import Exam, ExamQuestion, Question, StudentTopicMastery, Topic, User
from app.models.exam import SECTION_OF_TYPE
from app.models.question import USABLE
from app.services.exams import points_for

WEAK_SHARE, REASK_SHARE = 0.6, 0.1
WEAK_TOPICS = 3
RECENT_CORRECT_DAYS = 7
REASK_AFTER = timedelta(hours=24)


def target_difficulties(m: float | None) -> list[str]:
    if m is None or m < 0.4:
        return ["nb", "th"]
    if m < 0.7:
        return ["th", "vd"]
    return ["vd", "vdc"]


@dataclass
class Pick:
    question_id: uuid.UUID
    reason: str
    topic: str | None = None


@dataclass
class Plan:
    picks: list[Pick] = field(default_factory=list)
    note: str | None = None

    def ids(self) -> set:
        return {p.question_id for p in self.picks}


def _pool(db: Session, org_id, topic_path: str | None, exclude: set, subject_id=None) -> list[tuple[uuid.UUID, str | None]]:
    params = {"o": org_id, "usable": list(USABLE)}
    where = ["q.organization_id = :o", "q.status = any(:usable)"]
    if topic_path:
        where.append("exists (select 1 from question_topics qt join topics t on t.id = qt.topic_id "
                     "where qt.question_id = q.id and t.path <@ cast(:p as ltree))")
        params["p"] = topic_path
    if subject_id:
        where.append("q.subject_id = :s")
        params["s"] = subject_id
    rows = db.execute(text(f"select q.id, q.difficulty from questions q where {' and '.join(where)}"), params).all()
    return [(r[0], r[1]) for r in rows if r[0] not in exclude]


def _draw(rng: random.Random, pool: list[tuple], n: int, preferred: list[str]) -> list[uuid.UUID]:
    """Prefer the target difficulties (unknown difficulty counts as 'th'), then fall back to anything."""
    pref = [qid for qid, d in pool if (d or "th") in preferred]
    rest = [qid for qid, d in pool if (d or "th") not in preferred]
    rng.shuffle(pref)
    rng.shuffle(rest)
    return (pref + rest)[:n]


def build_plan(db: Session, org_id, student_id, count: int = 20, subject_id=None, grade=None, seed=None) -> Plan:
    rng = random.Random(seed)
    t = now()
    plan = Plan()
    recent_correct = set(db.scalars(text("""select question_id from answer_facts where organization_id=:o and student_id=:s
                                            and correct_ratio >= 1 and created_at > :since"""),
                                    {"o": org_id, "s": student_id, "since": t - timedelta(days=RECENT_CORRECT_DAYS)}))
    # wrong ≥ 24 h ago, still usable, and not answered correctly since
    n_reask_max = round(count * REASK_SHARE)
    usable_wrong = list(db.scalars(text("""
        select f.question_id from answer_facts f join questions q on q.id = f.question_id and q.status = any(:usable)
         where f.organization_id=:o and f.student_id=:s and f.correct_ratio < 1 and f.created_at < :cut
           and not exists (select 1 from answer_facts g where g.student_id=f.student_id and g.question_id=f.question_id
                           and g.correct_ratio >= 1 and g.created_at > f.created_at)
         group by f.question_id order by max(f.created_at) desc limit :n"""),
        {"o": org_id, "s": student_id, "cut": t - REASK_AFTER, "usable": list(USABLE), "n": n_reask_max}))
    exclude = set(recent_correct)

    mastery = db.execute(select(StudentTopicMastery, Topic).join(Topic, Topic.id == StudentTopicMastery.topic_id)
                         .where(StudentTopicMastery.student_id == student_id, StudentTopicMastery.organization_id == org_id)).all()
    if subject_id:
        mastery = [(m, tp) for m, tp in mastery if tp.subject_id == subject_id]
    ranked = sorted(mastery, key=lambda mt: mt[0].mastery)

    n_reask = min(len(usable_wrong), n_reask_max)
    for qid in usable_wrong[:n_reask]:
        plan.picks.append(Pick(qid, "Ôn lại câu từng làm sai"))
    exclude |= plan.ids()

    if not ranked:
        plan.note = "Chưa có dữ liệu làm bài — đề cân bằng các mạch kiến thức, lần sau sẽ theo điểm yếu của bạn."
        strands = db.scalars(select(Topic).where(Topic.organization_id == org_id, Topic.parent_id.is_(None),
                                                 *([Topic.subject_id == subject_id] if subject_id else []))).all()
        strands = [s for s in strands if _pool(db, org_id, s.path, exclude)]
        rng.shuffle(strands)
        per = max(1, (count - len(plan.picks)) // max(1, len(strands)))
        for s in strands:
            for qid in _draw(rng, _pool(db, org_id, s.path, exclude | plan.ids()), per, ["nb", "th"]):
                plan.picks.append(Pick(qid, "Làm quen", s.name))
        _fill(db, rng, plan, org_id, count, exclude, subject_id)
        return plan

    weak = [(m, tp) for m, tp in ranked if m.mastery < 0.8][:WEAK_TOPICS] or ranked[:WEAK_TOPICS]
    medium = [(m, tp) for m, tp in ranked if 0.5 <= m.mastery < 0.8 and (m, tp) not in weak]
    n_weak = round(count * WEAK_SHARE)
    n_medium = count - n_weak - len(plan.picks)

    def take(groups, n, reason):
        if not groups or n <= 0:
            return 0
        got = 0
        shares = [n // len(groups) + (1 if i < n % len(groups) else 0) for i in range(len(groups))]
        for (m, tp), k in zip(groups, shares):
            chosen = _draw(rng, _pool(db, org_id, tp.path, exclude | plan.ids()), k, target_difficulties(m.mastery))
            if len(chosen) < k and tp.parent_id:  # neighbours: widen to the parent subtree
                parent = db.get(Topic, tp.parent_id)
                chosen += _draw(rng, _pool(db, org_id, parent.path, exclude | plan.ids() | set(chosen)), k - len(chosen), target_difficulties(m.mastery))
            for qid in chosen:
                plan.picks.append(Pick(qid, reason, tp.name))
            got += len(chosen)
        return got

    got_weak = take(weak, n_weak, "Chuyên đề yếu")
    take(medium or weak, n_medium + (n_weak - got_weak), "Củng cố" if medium else "Chuyên đề yếu")
    _fill(db, rng, plan, org_id, count, exclude, subject_id)
    return plan


def _fill(db, rng, plan: Plan, org_id, count, exclude, subject_id) -> None:
    missing = count - len(plan.picks)
    if missing > 0:
        for qid in _draw(rng, _pool(db, org_id, None, exclude | plan.ids(), subject_id), missing, ["th", "vd"]):
            plan.picks.append(Pick(qid, "Bổ sung"))
    if len(plan.picks) < count and not plan.note:
        plan.note = f"Ngân hàng chỉ đủ {len(plan.picks)} câu phù hợp."


def create_exam(db: Session, org_id, student: User, plan: Plan, title: str | None = None, created_by=None) -> Exam:
    exam = Exam(organization_id=org_id, title=title or f"Đề ôn tập – {student.full_name}", source="adaptive", created_by=created_by,
                settings={"points_by_type": None, "scale_to": 10})
    from app.models.exam import DEFAULT_POINTS

    exam.settings = {"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10,
                     "adaptive": {"student_id": str(student.id), "note": plan.note,
                                  "plan": [{"question_id": str(p.question_id), "reason": p.reason, "topic": p.topic} for p in plan.picks]}}
    db.add(exam)
    db.flush()
    qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(plan.ids())))}
    order = sorted(plan.picks, key=lambda p: ["I", "II", "III", "IV"].index(SECTION_OF_TYPE.get(qs[p.question_id].type, "I")))
    for i, p in enumerate(order, start=1):
        q = qs[p.question_id]
        db.add(ExamQuestion(exam_id=exam.id, question_id=q.id, position=i, section=SECTION_OF_TYPE.get(q.type, "I"), points=points_for(exam, q.type)))
    db.flush()
    return exam


PRACTICE_MINUTES = 60


def start_practice(db: Session, scope, count: int = 20, subject_id=None):
    from app.core.errors import AppError, forbidden
    from app.services.assignments import new_attempt

    if scope.role != "student":
        raise forbidden()
    count = max(5, min(50, int(count)))
    plan = build_plan(db, scope.org_id, scope.user.id, count, subject_id)
    if not plan.picks:
        raise AppError("empty_bank", "Ngân hàng chưa có câu hỏi phù hợp", 409)
    exam = create_exam(db, scope.org_id, scope.user, plan, created_by=scope.user.id)
    att = new_attempt(db, scope.org_id, exam.id, scope.user.id, now() + timedelta(minutes=PRACTICE_MINUTES))
    return att, exam, plan


def assign_to_class(db: Session, scope, class_id, count: int, open_at, close_at, duration_minutes: int, title: str | None = None) -> int:
    from app.core.errors import validation
    from app.models import Assignment, AssignmentTarget
    from app.services import classes as class_service

    if close_at <= open_at:
        raise validation("Thời gian đóng phải sau thời gian mở", "close_at")
    if not 1 <= duration_minutes <= 600:
        raise validation("Thời lượng từ 1 đến 600 phút", "duration_minutes")
    count = max(5, min(50, int(count)))
    created = 0
    for u in class_service.members(db, scope, class_id):
        if u.role != "student" or not u.is_active:
            continue
        plan = build_plan(db, scope.org_id, u.id, count)
        if not plan.picks:
            continue
        exam = create_exam(db, scope.org_id, u, plan, title=title or f"Đề ôn cá nhân – {u.full_name}", created_by=scope.user.id)
        a = Assignment(organization_id=scope.org_id, exam_id=exam.id, title=title or "Đề ôn cá nhân", open_at=open_at, close_at=close_at,
                       duration_minutes=duration_minutes, max_attempts=1, results_policy="after_submit", created_by=scope.user.id)
        db.add(a)
        db.flush()
        db.add(AssignmentTarget(assignment_id=a.id, user_id=u.id))
        created += 1
    db.flush()
    return created


def plan_summary(exam: Exam) -> dict:
    ad = (exam.settings or {}).get("adaptive") or {}
    counts: dict = {}
    for p in ad.get("plan", []):
        key = (p["reason"], p.get("topic"))
        counts[key] = counts.get(key, 0) + 1
    return {"note": ad.get("note"), "groups": [{"reason": r, "topic": t, "count": n} for (r, t), n in counts.items()]}
