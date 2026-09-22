"""Question bank queries and mutations (US-06, A-10, A-11)."""
import uuid

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, validation
from app.deps import OrgScope
from app.models import Question, QuestionTag, QuestionTopic, SourceDocument, Tag, Topic
from app.models.question import DIFFICULTIES, QUESTION_TYPES, STATUSES, USABLE
from app.services import review
from app.services.question_quality import evaluate
from app.services.search_text import for_question, query as normalise_query

# Later features register checks such as "used by an exam" (fn(db, question_id) -> bool).
IN_USE_CHECKS: list = []


def filtered(db: Session, scope: OrgScope, *, q: str = "", subject_id=None, grade=None, semester_code=None, exam_kind=None,
             type=None, difficulty=None, status="usable", topic_id=None, tag_ids=None, document_id=None, topic_ids=None,
             school_year=None):
    """The bank's filter statement, shared by search, facets and the exam builder.

    `subject_id="none"` = questions without a subject. Tags: any of the chosen tags of one group,
    and every group (e.g. nguồn đề AND phương pháp). `school_year` is the source document's year.
    """
    stmt = select(Question).where(Question.organization_id == scope.org_id)
    if subject_id == "none":
        stmt = stmt.where(Question.subject_id.is_(None))
        subject_id = None
    if status == "usable":
        stmt = stmt.where(Question.status.in_(USABLE))
    elif status and status != "all":
        stmt = stmt.where(Question.status == status)
    for col, val in ((Question.subject_id, subject_id), (Question.grade, grade), (Question.semester_code, semester_code),
                     (Question.exam_kind, exam_kind), (Question.type, type), (Question.difficulty, difficulty),
                     (Question.source_document_id, document_id)):
        if val not in (None, ""):
            stmt = stmt.where(col == val)
    roots_ids = [t for t in [topic_id, *(topic_ids or [])] if t]
    if roots_ids:
        # each chosen node includes its whole subtree; several nodes are OR-ed
        roots = db.scalars(select(Topic).where(Topic.id.in_(roots_ids), Topic.organization_id == scope.org_id)).all()
        if len(roots) != len(set(roots_ids)):
            raise validation("Chuyên đề không hợp lệ", "topic_ids")
        stmt = stmt.where(exists(
            select(QuestionTopic.question_id).join(Topic, Topic.id == QuestionTopic.topic_id)
            .where(QuestionTopic.question_id == Question.id,
                   or_(*[Topic.path.op("<@")(func.text2ltree(r.path)) for r in roots]))
        ))
    if tag_ids:
        groups: dict[str, list] = {}
        for t in db.scalars(select(Tag).where(Tag.id.in_(tag_ids), Tag.organization_id == scope.org_id)):
            groups.setdefault(t.group, []).append(t.id)
        if sum(len(v) for v in groups.values()) != len(set(tag_ids)):
            raise validation("Tag không hợp lệ", "tag_ids")
        for ids in groups.values():
            stmt = stmt.where(exists(select(QuestionTag.question_id).where(QuestionTag.question_id == Question.id, QuestionTag.tag_id.in_(ids))))
    if school_year:
        stmt = stmt.where(exists(select(SourceDocument.id).where(SourceDocument.id == Question.source_document_id,
                                                                 SourceDocument.meta["school_year"].astext == school_year)))
    needle = normalise_query(q) if q else ""
    if needle:
        stmt = stmt.where(Question.search_text.contains(needle) | (func.similarity(Question.search_text, needle) > 0.3))
    return stmt, needle


def search(db: Session, scope: OrgScope, *, page: int = 1, page_size: int = 20, **filters):
    stmt, needle = filtered(db, scope, **filters)
    order = [Question.created_at.desc(), Question.number]
    if needle:
        order = [func.similarity(Question.search_text, needle).desc()] + order
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(*order).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def facets(db: Session, scope: OrgScope, **filters) -> dict:
    """Counts for the filter sheet (subject-scoped-bank ADR-02): each facet applies every filter but its own."""
    def ids(*drop: str):
        f = {**filters, **{k: None for k in drop}}
        stmt, _ = filtered(db, scope, **f)
        return stmt.with_only_columns(Question.id).subquery()

    def grouped(col, *drop: str) -> dict:
        sub = ids(*drop)
        rows = db.execute(select(col, func.count()).select_from(Question).join(sub, sub.c.id == Question.id).group_by(col)).all()
        return {("none" if k is None else str(k)): n for k, n in rows}

    out = {
        "subjects": grouped(Question.subject_id, "subject_id", "topic_id", "topic_ids", "tag_ids"),
        "types": grouped(Question.type, "type"),
        "difficulties": grouped(Question.difficulty, "difficulty"),
        "grades": grouped(Question.grade, "grade"),
    }
    sub = ids("semester_code", "exam_kind")
    out["periods"] = {f"{s or ''}|{k or ''}": n for s, k, n in db.execute(
        select(Question.semester_code, Question.exam_kind, func.count()).join(sub, sub.c.id == Question.id)
        .where((Question.semester_code.isnot(None)) | (Question.exam_kind.isnot(None)))
        .group_by(Question.semester_code, Question.exam_kind)).all()}
    sub = ids("school_year")
    year = SourceDocument.meta["school_year"].astext
    out["school_years"] = {y: n for y, n in db.execute(
        select(year, func.count()).select_from(Question).join(sub, sub.c.id == Question.id)
        .join(SourceDocument, SourceDocument.id == Question.source_document_id).where(year.isnot(None)).group_by(year)).all()}
    sub = ids("tag_ids")
    out["tags"] = {str(t): n for t, n in db.execute(
        select(QuestionTag.tag_id, func.count()).join(sub, sub.c.id == QuestionTag.question_id).group_by(QuestionTag.tag_id)).all()}
    # topics: questions in each node's subtree (a question counted once per node)
    sub = ids("topic_id", "topic_ids")
    node, leaf = Topic.__table__.alias("node"), Topic.__table__.alias("leaf")
    stmt = (select(node.c.id, func.count(func.distinct(QuestionTopic.question_id)))
            .select_from(node)
            .join(leaf, leaf.c.path.op("<@")(node.c.path))
            .join(QuestionTopic, QuestionTopic.topic_id == leaf.c.id)
            .join(sub, sub.c.id == QuestionTopic.question_id)
            .where(node.c.organization_id == scope.org_id)
            .group_by(node.c.id))
    if filters.get("subject_id") and filters["subject_id"] != "none":
        stmt = stmt.where(node.c.subject_id == filters["subject_id"])
    out["topics"] = {str(t): n for t, n in db.execute(stmt).all()}
    return out


def search_ids(db: Session, scope: OrgScope, **filters) -> list:
    stmt, _ = filtered(db, scope, **filters)
    return list(db.scalars(stmt.with_only_columns(Question.id).order_by(Question.id)))


def release_duplicates_of(db: Session, gone) -> None:
    """Before questions are deleted: copies marked "duplicate" of them go back to review
    (otherwise they stay hidden as duplicates of nothing). `gone` selects the question ids."""
    from sqlalchemy import update

    db.execute(update(Question).where(Question.duplicate_of.in_(gone), Question.status == "duplicate")
               .values(status="needs_review", duplicate_of=None).execution_options(synchronize_session=False))


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
    release_duplicates_of(db, select(Question.id).where(Question.id == q.id))
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
            if review.blocking_manual(q.issues or []):
                raise AppError("has_blocking_issues", f"Câu {q.number or ''} còn lỗi: " + ", ".join(review.blocking_manual(q.issues)), 409)
            review.settle(q)
            q.status, q.spot_check = "approved", False
            review._mark_reviewed(q, scope)
        elif status == "rejected":
            q.status, q.spot_check = "rejected", False
        review.record(db, scope, q, "bulk", before, review.snapshot(q))
    db.flush()
    return len(qs)


VALID_STATUS_FILTERS = ("usable", "all") + STATUSES
