"""Assignments: who takes which exam when (US-02, A-05, A-06, A-10)."""
from datetime import timedelta
import random
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden, not_found, validation
from app.core.security import now
from app.deps import OrgScope
from app.models import Assignment, AssignmentTarget, Attempt, ClassMember, Exam, ExamQuestion, Question, SchoolClass, User
from app.models.exam import RESULTS_POLICIES
from app.services.paging import Col, ListParams, paginate
from app.services import exams

GRACE = timedelta(seconds=30)


def get(db: Session, scope: OrgScope, aid) -> Assignment:
    a = db.get(Assignment, aid)
    if a is None or a.organization_id != scope.org_id:
        raise not_found("Không tìm thấy bài được giao")
    return a


def student_ids(db: Session, a: Assignment) -> set:
    targets = db.scalars(select(AssignmentTarget).where(AssignmentTarget.assignment_id == a.id)).all()
    ids = {t.user_id for t in targets if t.user_id}
    class_ids = [t.class_id for t in targets if t.class_id]
    if class_ids:
        ids |= set(db.scalars(select(ClassMember.user_id).join(User, User.id == ClassMember.user_id)
                              .where(ClassMember.class_id.in_(class_ids), User.role == "student", User.is_active.is_(True))))
    return ids


def _validate(db: Session, scope: OrgScope, data: dict) -> None:
    if data["close_at"] <= data["open_at"]:
        raise validation("Thời gian đóng phải sau thời gian mở", "close_at")
    if not 1 <= data["duration_minutes"] <= 600:
        raise validation("Thời lượng từ 1 đến 600 phút", "duration_minutes")
    if not 1 <= data.get("max_attempts", 1) <= 20:
        raise validation("Số lượt làm từ 1 đến 20", "max_attempts")
    if data.get("results_policy", "after_submit") not in RESULTS_POLICIES:
        raise validation("Chính sách xem kết quả không hợp lệ", "results_policy")


def create(db: Session, scope: OrgScope, exam_id, data: dict, class_ids: list, user_ids: list) -> Assignment:
    exam = exams.get(db, scope, exam_id)
    if not db.scalar(select(func.count()).select_from(ExamQuestion).where(ExamQuestion.exam_id == exam.id)):
        raise validation("Đề chưa có câu hỏi", "exam_id")
    _validate(db, scope, data)
    if not class_ids and not user_ids:
        raise validation("Chọn ít nhất một lớp hoặc học sinh", "class_ids")
    for cid in class_ids:
        c = db.get(SchoolClass, cid)
        if c is None or c.organization_id != scope.org_id:
            raise validation("Lớp không hợp lệ", "class_ids")
    for uid in user_ids:
        u = db.get(User, uid)
        if u is None or u.organization_id != scope.org_id or u.role != "student":
            raise validation("Học sinh không hợp lệ", "user_ids")
    a = Assignment(organization_id=scope.org_id, exam_id=exam.id, title=(data.get("title") or exam.title).strip(),
                   open_at=data["open_at"], close_at=data["close_at"], duration_minutes=data["duration_minutes"],
                   max_attempts=data.get("max_attempts", 1), shuffle_questions=data.get("shuffle_questions", True),
                   shuffle_options=data.get("shuffle_options", True), results_policy=data.get("results_policy", "after_submit"),
                   created_by=scope.user.id)
    db.add(a)
    db.flush()
    for cid in class_ids:
        db.add(AssignmentTarget(assignment_id=a.id, class_id=cid))
    for uid in user_ids:
        db.add(AssignmentTarget(assignment_id=a.id, user_id=uid))
    db.flush()
    return a


def update(db: Session, scope: OrgScope, aid, data: dict) -> Assignment:
    a = get(db, scope, aid)
    merged = {"open_at": a.open_at, "close_at": a.close_at, "duration_minutes": a.duration_minutes, "max_attempts": a.max_attempts,
              "results_policy": a.results_policy, **{k: v for k, v in data.items() if v is not None}}
    _validate(db, scope, merged)
    for k in ("title", "open_at", "close_at", "duration_minutes", "max_attempts", "shuffle_questions", "shuffle_options", "results_policy"):
        if data.get(k) is not None:
            setattr(a, k, data[k])
    return a


def delete(db: Session, scope: OrgScope, aid) -> None:
    a = get(db, scope, aid)
    if db.scalar(select(func.count()).select_from(Attempt).where(Attempt.assignment_id == a.id)):
        raise AppError("assignment_in_use", "Đã có học sinh làm bài — không thể xóa, hãy đóng sớm", 409)
    db.delete(a)


ASSIGNMENT_COLS = {
    "title": Col(Assignment.title),
    "exam_id": Col(Assignment.exam_id, "uuid"),
    "open_at": Col(Assignment.open_at, "date"),
    "close_at": Col(Assignment.close_at, "date"),
    "duration_minutes": Col(Assignment.duration_minutes, "number"),
}


def list_for_staff(db: Session, scope: OrgScope, params: ListParams):
    stmt = select(Assignment).where(Assignment.organization_id == scope.org_id)
    rows, total = paginate(db, stmt, params, ASSIGNMENT_COLS, search=[Assignment.title], default_sort=[Assignment.open_at.desc(), Assignment.id])
    out = []
    for a in rows:
        targets = student_ids(db, a)
        submitted = db.scalar(select(func.count(func.distinct(Attempt.student_id))).where(Attempt.assignment_id == a.id, Attempt.status == "submitted"))
        classes = db.scalars(select(SchoolClass.name).join(AssignmentTarget, AssignmentTarget.class_id == SchoolClass.id)
                             .where(AssignmentTarget.assignment_id == a.id)).all()
        out.append({"assignment": a, "students": len(targets), "submitted": submitted or 0, "classes": list(classes)})
    return out, total


def window_state(a: Assignment) -> str:
    t = now()
    return "upcoming" if t < a.open_at else "closed" if t >= a.close_at else "open"


def me_assignments(db: Session, scope: OrgScope) -> list[dict]:
    if scope.role != "student":
        raise forbidden()
    class_ids = select(ClassMember.class_id).where(ClassMember.user_id == scope.user.id)
    stmt = (select(Assignment).join(AssignmentTarget, AssignmentTarget.assignment_id == Assignment.id)
            .where(Assignment.organization_id == scope.org_id,
                   or_(AssignmentTarget.user_id == scope.user.id, AssignmentTarget.class_id.in_(class_ids)))
            .distinct().order_by(Assignment.open_at))
    out = []
    for a in db.scalars(stmt):
        attempts = db.scalars(select(Attempt).where(Attempt.assignment_id == a.id, Attempt.student_id == scope.user.id)
                              .order_by(Attempt.started_at.desc())).all()
        out.append({"assignment": a, "state": window_state(a), "attempts": attempts,
                    "attempts_left": max(0, a.max_attempts - len(attempts))})
    return out


def start(db: Session, scope: OrgScope, aid) -> Attempt:
    from app.services import attempts as attempt_service

    if scope.role != "student":
        raise forbidden()
    a = get(db, scope, aid)
    if scope.user.id not in student_ids(db, a):
        raise not_found("Không tìm thấy bài được giao")
    state = window_state(a)
    if state == "upcoming":
        raise AppError("not_open", "Bài chưa mở", 409)
    if state == "closed":
        raise AppError("closed", "Bài đã đóng", 409)
    current = db.scalar(select(Attempt).where(Attempt.assignment_id == a.id, Attempt.student_id == scope.user.id, Attempt.status == "in_progress"))
    if current is not None:
        if attempt_service.finalize_if_expired(db, current):
            raise AppError("closed", "Lượt làm đã hết giờ", 409)
        return current
    used = db.scalar(select(func.count()).select_from(Attempt).where(Attempt.assignment_id == a.id, Attempt.student_id == scope.user.id))
    if used >= a.max_attempts:
        raise AppError("no_attempts_left", "Bạn đã dùng hết lượt làm", 409)
    deadline = min(now() + timedelta(minutes=a.duration_minutes), a.close_at)
    return new_attempt(db, scope.org_id, a.exam_id, scope.user.id, deadline, a.id, a.shuffle_questions, a.shuffle_options)


def new_attempt(db: Session, org_id, exam_id, student_id, deadline, assignment_id=None, shuffle_q=True, shuffle_o=True) -> Attempt:
    rows = db.execute(select(ExamQuestion, Question.type, Question.options).join(Question, Question.id == ExamQuestion.question_id)
                      .where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.position)).all()
    rng = random.Random()
    order: list[str] = []
    for section in dict.fromkeys(eq.section for eq, _, _ in rows):  # keep sections in order, shuffle inside
        ids = [str(eq.question_id) for eq, _, _ in rows if eq.section == section]
        if shuffle_q:
            rng.shuffle(ids)
        order += ids
    option_orders = {}
    if shuffle_o:
        for eq, qtype, options in rows:
            if qtype == "mcq" and options:
                labels = [o["label"] for o in options]
                rng.shuffle(labels)
                option_orders[str(eq.question_id)] = labels
    att = Attempt(organization_id=org_id, assignment_id=assignment_id, exam_id=exam_id, student_id=student_id, deadline_at=deadline,
                  question_order=order, option_orders=option_orders, max_score=sum(eq.points for eq, _, _ in rows))
    db.add(att)
    db.flush()
    return att
