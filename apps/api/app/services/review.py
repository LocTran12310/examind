"""Review workflow over questions.status (question-review ADR-03)."""
from datetime import UTC, datetime
import uuid

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden, not_found, validation
from app.deps import OrgScope
from app.models import Organization, Question, QuestionTag, QuestionTopic, ReviewEvent, SourceDocument, Tag, Topic, User
from app.services.question_quality import blocking, reevaluate, triage_status
from app.services.search_text import for_question

STATUS_KEYS = ("auto_approved", "needs_review", "approved", "rejected", "duplicate")


def document_counts(db: Session, scope: OrgScope, mine: bool = False, doc_id=None) -> list[dict]:
    cols = [func.count(case((Question.status == s, 1))).label(s) for s in STATUS_KEYS]
    spot = func.count(case((and_(Question.spot_check.is_(True), Question.status == "auto_approved"), 1))).label("spot_pending")
    stmt = (select(SourceDocument, func.count(Question.id).label("total"), *cols, spot)
            .outerjoin(Question, Question.source_document_id == SourceDocument.id)
            .where(SourceDocument.organization_id == scope.org_id, SourceDocument.status == "parsed")
            .group_by(SourceDocument.id).order_by(SourceDocument.created_at.desc()))
    if mine:
        stmt = stmt.where(SourceDocument.assigned_to == scope.user.id)
    if doc_id:
        stmt = stmt.where(SourceDocument.id == doc_id)
    users = {}
    out = []
    for row in db.execute(stmt):
        doc = row[0]
        counts = {s: getattr(row, s) for s in STATUS_KEYS}
        done = counts["approved"] + counts["rejected"] + counts["duplicate"] + counts["auto_approved"] - row.spot_pending
        if doc.assigned_to and doc.assigned_to not in users:
            u = db.get(User, doc.assigned_to)
            users[doc.assigned_to] = u.full_name if u else None
        out.append({"document": doc, "total": row.total, "counts": counts, "spot_pending": row.spot_pending,
                    "progress": round(done / row.total, 2) if row.total else 1.0,
                    "assigned_to": doc.assigned_to, "assigned_name": users.get(doc.assigned_to)})
    return out


def assign(db: Session, scope: OrgScope, doc_id, user_id) -> SourceDocument:
    if scope.role != "org_admin":
        raise forbidden()
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    if user_id is not None:
        u = db.get(User, uuid.UUID(str(user_id)))
        if u is None or u.organization_id != scope.org_id or u.role not in ("teacher", "org_admin"):
            raise validation("Chỉ giao cho giáo viên của trung tâm", "assigned_to")
    doc.assigned_to = uuid.UUID(str(user_id)) if user_id else None
    return doc


# ------------------------------------------------------------------ queue and actions

GROUP_ORDER = ["thiếu đáp án", "thiếu phương án", "không nhận ra phương án", "đáp án không khớp bảng đáp án",
               "đáp án không khớp định dạng", "OCR", "AI không phản hồi"]
SPOT_WINDOW, SPOT_FAILS, THRESHOLD_STEP, THRESHOLD_MAX = 20, 2, 0.05, 0.95


def get_question(db: Session, scope: OrgScope, qid) -> Question:
    q = db.get(Question, qid)
    if q is None or q.organization_id != scope.org_id:
        raise not_found("Không tìm thấy câu hỏi")
    return q


def group_of(q: Question) -> str:
    if q.status == "auto_approved" and q.spot_check:
        return "Kiểm tra ngẫu nhiên"
    for g in GROUP_ORDER:
        if g in (q.issues or []):
            return g
    b = blocking(q.issues or [])
    return b[0] if b else "Độ tin cậy thấp"


def queue(db: Session, scope: OrgScope, doc_id) -> list[Question]:
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    qs = db.scalars(select(Question).where(
        Question.source_document_id == doc.id,
        (Question.status == "needs_review") | (Question.spot_check.is_(True) & (Question.status == "auto_approved")),
    )).all()
    order = {g: i for i, g in enumerate(GROUP_ORDER)}

    def key(q):
        g = group_of(q)
        return (1 if g == "Kiểm tra ngẫu nhiên" else 0, order.get(g, len(order)), q.part or "", q.number or 0)

    return sorted(qs, key=key)


def snapshot(q: Question) -> dict:
    return {"status": q.status, "answer": q.answer, "confidence": q.confidence, "issues": list(q.issues or [])}


def record(db: Session, scope: OrgScope, q: Question | None, action: str, before: dict | None, after: dict | None) -> None:
    db.add(ReviewEvent(organization_id=scope.org_id, question_id=q.id if q else None, user_id=scope.user.id,
                       action=action, before=before, after=after))


def _mark_reviewed(q: Question, scope: OrgScope) -> None:
    q.reviewed_by, q.reviewed_at = scope.user.id, datetime.now(UTC)


def act(db: Session, scope: OrgScope, qid, action: str) -> Question:
    q = get_question(db, scope, qid)
    before = snapshot(q)
    was_spot = q.spot_check and q.status == "auto_approved"
    if action == "approve":
        if blocking(q.issues or []):
            raise AppError("has_blocking_issues", "Câu còn lỗi: " + ", ".join(blocking(q.issues)), 409)
        q.status, q.spot_check = "approved", False
        _mark_reviewed(q, scope)
        record(db, scope, q, "spot_ok" if was_spot else "approve", before, snapshot(q))
    elif action == "reject":
        q.status, q.spot_check = "rejected", False
        _mark_reviewed(q, scope)
        record(db, scope, q, "spot_fail" if was_spot else "reject", before, snapshot(q))
        if was_spot:
            _spot_feedback(db, scope)
    elif action == "restore":
        if q.status not in ("rejected", "duplicate"):
            raise AppError("invalid_state", "Chỉ khôi phục câu đã loại hoặc trùng", 409)
        q.duplicate_of = None
        q.status = triage_status(q.confidence, q.issues or [], _threshold(db, scope))
        record(db, scope, q, "restore", before, snapshot(q))
    elif action == "skip":
        record(db, scope, q, "skip", None, None)
    else:
        raise AppError("validation_error", "Thao tác không hợp lệ", 422)
    db.flush()
    return q


def _threshold(db: Session, scope: OrgScope) -> float:
    from app.services.ingestion_settings import org_defaults

    return float(org_defaults(db, scope.org_id)["threshold"])


def _spot_feedback(db: Session, scope: OrgScope) -> None:
    """A-07: two failed spot checks in the last twenty make auto-approval stricter."""
    recent = db.scalars(select(ReviewEvent.action).where(ReviewEvent.organization_id == scope.org_id,
                                                         ReviewEvent.action.in_(("spot_ok", "spot_fail")))
                        .order_by(ReviewEvent.created_at.desc()).limit(SPOT_WINDOW)).all()
    if sum(a == "spot_fail" for a in recent) < SPOT_FAILS:
        return
    org = db.get(Organization, scope.org_id)
    settings = dict(org.settings or {})
    ing = dict(settings.get("ingestion", {}))
    old = float(ing.get("threshold", 0.85))
    new = min(THRESHOLD_MAX, round(old + THRESHOLD_STEP, 2))
    if new != old:
        ing["threshold"] = new
        settings["ingestion"] = ing
        org.settings = settings
        record(db, scope, None, "triage", {"threshold": old}, {"threshold": new})


def _valid_answer(qtype: str, options: list[dict], answer) -> dict | None:
    if answer in (None, {}, ""):
        return None
    if not isinstance(answer, dict):
        raise AppError("validation_error", "Đáp án không hợp lệ", 422, {"answer": "Đáp án không hợp lệ"})
    labels = {o.get("label") for o in options}
    if qtype == "mcq" and answer.get("key") not in labels:
        raise AppError("validation_error", "Đáp án phải là một phương án", 422, {"answer": "Đáp án phải là một phương án"})
    if qtype == "true_false":
        return {k: v for k, v in answer.items() if k in labels and isinstance(v, bool)}
    return answer


def edit(db: Session, scope: OrgScope, qid, changes: dict) -> Question:
    q = get_question(db, scope, qid)
    before = snapshot(q)
    was_spot = q.spot_check and q.status == "auto_approved"
    content_changed = False
    if changes.get("type") is not None:
        if changes["type"] not in ("mcq", "true_false", "short_answer", "essay"):
            raise AppError("validation_error", "Loại câu không hợp lệ", 422, {"type": "Loại câu không hợp lệ"})
        q.type, content_changed = changes["type"], True
    for f in ("stem", "solution"):
        if changes.get(f) is not None:
            setattr(q, f, changes[f])
            content_changed = True
    if changes.get("options") is not None:
        q.options = [{k: v for k, v in o.items() if k in ("label", "content", "is_true")} for o in changes["options"]]
        content_changed = True
    if "answer" in changes and changes["answer"] is not None:
        q.answer = _valid_answer(q.type, q.options or [], changes["answer"])
        if q.type == "true_false" and q.answer:
            q.options = [{**o, "is_true": q.answer.get(o["label"])} for o in q.options]
        q.answer_source = "manual"
        content_changed = True
    for f in ("difficulty", "grade"):
        if changes.get(f) is not None:
            setattr(q, f, changes[f] or None)
    if changes.get("subject_id") is not None:
        from app.models import Subject

        subject = db.get(Subject, uuid.UUID(str(changes["subject_id"])))
        if subject is None or subject.organization_id != scope.org_id:
            raise AppError("validation_error", "Môn học không hợp lệ", 422, {"subject_id": "Môn học không hợp lệ"})
        q.subject_id = subject.id
    if changes.get("topic_ids") is not None or changes.get("primary_topic_id") is not None:
        set_topics(db, scope, q, changes.get("topic_ids"), changes.get("primary_topic_id"))
    if changes.get("tag_ids") is not None:
        set_tags(db, scope, q, changes["tag_ids"])
    if content_changed:
        reevaluate(q)
        q.search_text = for_question(q.stem, q.options)  # status unchanged: the teacher approves explicitly (Enter)
    action = "answer" if set(changes) & {"answer"} and not (set(changes) & {"stem", "options", "solution"}) else "edit"
    if was_spot and content_changed:
        q.spot_check = False
        q.status = "approved" if not blocking(q.issues) else "needs_review"
        _mark_reviewed(q, scope)
        record(db, scope, q, "spot_fail", before, snapshot(q))
        _spot_feedback(db, scope)
    else:
        record(db, scope, q, action, before, snapshot(q))
    db.flush()
    return q


def set_topics(db: Session, scope: OrgScope, q: Question, topic_ids, primary_id) -> None:
    ids = [uuid.UUID(str(t)) for t in (topic_ids if topic_ids is not None else ([primary_id] if primary_id else []))]
    if primary_id and uuid.UUID(str(primary_id)) not in ids:
        ids.insert(0, uuid.UUID(str(primary_id)))
    valid = set(db.scalars(select(Topic.id).where(Topic.id.in_(ids), Topic.organization_id == scope.org_id))) if ids else set()
    if set(ids) - valid:
        raise AppError("validation_error", "Chuyên đề không hợp lệ", 422, {"topic_ids": "Chuyên đề không hợp lệ"})
    db.execute(QuestionTopic.__table__.delete().where(QuestionTopic.question_id == q.id))
    primary = uuid.UUID(str(primary_id)) if primary_id else (ids[0] if ids else None)
    for tid in ids:
        db.add(QuestionTopic(question_id=q.id, topic_id=tid, is_primary=tid == primary, source="manual", score=1.0))
    record(db, scope, q, "topic", None, {"topics": [str(i) for i in ids], "primary": str(primary) if primary else None})


def set_tags(db: Session, scope: OrgScope, q: Question, tag_ids) -> None:
    ids = [uuid.UUID(str(t)) for t in tag_ids]
    valid = set(db.scalars(select(Tag.id).where(Tag.id.in_(ids), Tag.organization_id == scope.org_id))) if ids else set()
    if set(ids) - valid:
        raise AppError("validation_error", "Tag không hợp lệ", 422, {"tag_ids": "Tag không hợp lệ"})
    db.execute(QuestionTag.__table__.delete().where(QuestionTag.question_id == q.id))
    for tid in ids:
        db.add(QuestionTag(question_id=q.id, tag_id=tid))


def apply_answer_key(db: Session, scope: OrgScope, doc_id, text: str) -> dict:
    from app.services import answer_key

    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    key = answer_key.parse(text)
    qs = db.scalars(select(Question).where(Question.source_document_id == doc.id, Question.type == "mcq")).all()
    by_part = {(q.part, q.number): q for q in qs}
    by_num: dict[int, list[Question]] = {}
    for q in qs:
        by_num.setdefault(q.number, []).append(q)
    applied, approved, unmatched = 0, 0, []
    for (part, n), letter in sorted(key.items(), key=lambda kv: ((kv[0][0] or ""), kv[0][1])):
        q = by_part.get((part, n)) or (by_num.get(n, [None])[0] if len(by_num.get(n, [])) == 1 else None)
        if q is None or letter not in {o.get("label") for o in q.options or []}:
            unmatched.append(n)
            continue
        if q.status == "approved":
            continue
        before = snapshot(q)
        q.answer, q.answer_source = {"key": letter}, "manual"
        reevaluate(q)
        applied += 1
        if q.status == "needs_review" and not blocking(q.issues):
            q.status = "approved"
            _mark_reviewed(q, scope)
            approved += 1
        record(db, scope, q, "answer", before, snapshot(q))
    db.flush()
    return {"applied": applied, "approved": approved, "unmatched": unmatched}


def approve_confident(db: Session, scope: OrgScope, doc_id) -> int:
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    qs = db.scalars(select(Question).where(Question.source_document_id == doc.id, Question.status == "auto_approved",
                                           Question.spot_check.is_(False))).all()
    for q in qs:
        q.status = "approved"
        _mark_reviewed(q, scope)
    if qs:
        record(db, scope, None, "bulk", {"status": "auto_approved"}, {"status": "approved", "count": len(qs), "document": str(doc.id)})
    db.flush()
    return len(qs)
