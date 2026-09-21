"""Question bank queries and mutations (US-06, A-10, A-11)."""
import uuid

from sqlalchemy import exists, func, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError, validation
from app.deps import OrgScope
from app.models import Question, QuestionTag, QuestionTopic, Topic
from app.models.question import DIFFICULTIES, QUESTION_TYPES, STATUSES, USABLE
from app.services import review
from app.services.question_quality import evaluate
from app.services.search_text import for_question, query as normalise_query

# Later features register checks such as "used by an exam" (fn(db, question_id) -> bool).
IN_USE_CHECKS: list = []


def search(db: Session, scope: OrgScope, *, q: str = "", subject_id=None, grade=None, semester_code=None, exam_kind=None,
           type=None, difficulty=None, status="usable", topic_id=None, tag_ids=None, document_id=None,
           page: int = 1, page_size: int = 20):
    stmt = select(Question).where(Question.organization_id == scope.org_id)
    if status == "usable":
        stmt = stmt.where(Question.status.in_(USABLE))
    elif status and status != "all":
        stmt = stmt.where(Question.status == status)
    for col, val in ((Question.subject_id, subject_id), (Question.grade, grade), (Question.semester_code, semester_code),
                     (Question.exam_kind, exam_kind), (Question.type, type), (Question.difficulty, difficulty),
                     (Question.source_document_id, document_id)):
        if val not in (None, ""):
            stmt = stmt.where(col == val)
    if topic_id:
        root = db.get(Topic, topic_id)
        if root is None or root.organization_id != scope.org_id:
            raise validation("Chuyên đề không hợp lệ", "topic_id")
        stmt = stmt.where(exists(
            select(QuestionTopic.question_id).join(Topic, Topic.id == QuestionTopic.topic_id)
            .where(QuestionTopic.question_id == Question.id, text("topics.path <@ cast(:root_path as ltree)"))
        ).params(root_path=root.path))
    if tag_ids:
        stmt = stmt.where(exists(select(QuestionTag.question_id).where(QuestionTag.question_id == Question.id, QuestionTag.tag_id.in_(tag_ids))))
    needle = normalise_query(q) if q else ""
    order = [Question.created_at.desc(), Question.number]
    if needle:
        stmt = stmt.where(Question.search_text.contains(needle) | (func.similarity(Question.search_text, needle) > 0.3))
        order = [func.similarity(Question.search_text, needle).desc()] + order
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(*order).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def create(db: Session, scope: OrgScope, data: dict) -> Question:
    qtype = data.get("type") or "mcq"
    if qtype not in QUESTION_TYPES:
        raise validation("Loại câu không hợp lệ", "type")
    if data.get("difficulty") and data["difficulty"] not in DIFFICULTIES:
        raise validation("Mức độ không hợp lệ", "difficulty")
    q = Question(organization_id=scope.org_id, type=qtype, stem=data.get("stem") or "", options=data.get("options") or [],
                 solution=data.get("solution") or "", difficulty=data.get("difficulty"), grade=data.get("grade"),
                 subject_id=data.get("subject_id"), semester_code=data.get("semester_code"), exam_kind=data.get("exam_kind"),
                 source="manual", status="approved", issues=[], answer_source="manual")
    db.add(q)
    db.flush()
    if data.get("answer"):
        q.answer = review._valid_answer(q.type, q.options, data["answer"])
    q.issues, q.confidence = evaluate(q.type, q.stem, q.options, q.answer, q.solution)
    if review.blocking(q.issues):
        raise AppError("has_blocking_issues", "Câu còn lỗi: " + ", ".join(review.blocking(q.issues)), 422)
    q.search_text = for_question(q.stem, q.options)
    review._mark_reviewed(q, scope)
    if data.get("primary_topic_id") or data.get("topic_ids"):
        review.set_topics(db, scope, q, data.get("topic_ids"), data.get("primary_topic_id"))
    if data.get("tag_ids"):
        review.set_tags(db, scope, q, data["tag_ids"])
    review.record(db, scope, q, "edit", None, review.snapshot(q))
    db.flush()
    return q


def delete(db: Session, scope: OrgScope, qid) -> None:
    q = review.get_question(db, scope, qid)
    if any(check(db, q.id) for check in IN_USE_CHECKS):
        raise AppError("question_in_use", "Câu hỏi đang được dùng trong đề — hãy loại thay vì xóa", 409)
    review.record(db, scope, q, "reject", review.snapshot(q), {"deleted": True})
    db.flush()
    db.delete(q)


def bulk(db: Session, scope: OrgScope, ids: list, changes: dict) -> int:
    qs = db.scalars(select(Question).where(Question.id.in_([uuid.UUID(str(i)) for i in ids]), Question.organization_id == scope.org_id)).all()
    if len(qs) != len(set(ids)):
        raise AppError("not_found", "Một số câu hỏi không tồn tại", 404)
    status = changes.get("status")
    if status and status not in ("approved", "rejected"):
        raise validation("Chỉ có thể duyệt hoặc loại hàng loạt", "status")
    if changes.get("difficulty") and changes["difficulty"] not in DIFFICULTIES:
        raise validation("Mức độ không hợp lệ", "difficulty")
    for q in qs:
        before = review.snapshot(q)
        if changes.get("difficulty"):
            q.difficulty = changes["difficulty"]
        if changes.get("primary_topic_id"):
            review.set_topics(db, scope, q, None, changes["primary_topic_id"])
        if changes.get("add_tag_ids"):
            current = set(db.scalars(select(QuestionTag.tag_id).where(QuestionTag.question_id == q.id)))
            review.set_tags(db, scope, q, list(current | {uuid.UUID(str(t)) for t in changes["add_tag_ids"]}))
        if status == "approved":
            if review.blocking(q.issues or []):
                raise AppError("has_blocking_issues", f"Câu {q.number or ''} còn lỗi: " + ", ".join(review.blocking(q.issues)), 409)
            q.status, q.spot_check = "approved", False
            review._mark_reviewed(q, scope)
        elif status == "rejected":
            q.status, q.spot_check = "rejected", False
        review.record(db, scope, q, "bulk", before, review.snapshot(q))
    db.flush()
    return len(qs)


VALID_STATUS_FILTERS = ("usable", "all") + STATUSES
