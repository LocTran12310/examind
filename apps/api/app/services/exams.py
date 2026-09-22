"""Exam builder: blueprints, manual edits, points (US-01, A-01, A-04)."""
import random
import uuid

from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found, validation
from app.deps import OrgScope
from app.models import Attempt, Exam, ExamQuestion, Question, Subject
from app.models.exam import DEFAULT_POINTS, SECTION_OF_TYPE
from app.models.question import USABLE
from app.services.paging import Col, ListParams, paginate
from app.services import bank

SECTION_ORDER = ["I", "II", "III", "IV"]


def get(db: Session, scope: OrgScope, exam_id) -> Exam:
    e = db.get(Exam, exam_id)
    if e is None or e.organization_id != scope.org_id:
        raise not_found("Không tìm thấy đề")
    return e


def points_for(exam: Exam, qtype: str) -> float:
    return float((exam.settings or {}).get("points_by_type", DEFAULT_POINTS).get(qtype, DEFAULT_POINTS.get(qtype, 1.0)))


_COUNTS = (select(ExamQuestion.exam_id, func.count().label("n"), func.coalesce(func.sum(ExamQuestion.points), 0).label("pts"))
           .group_by(ExamQuestion.exam_id).subquery())
EXAM_COLS = {
    "title": Col(Exam.title),
    "grade": Col(Exam.grade, "number"),
    "source": Col(Exam.source, "exact"),
    "subject_id": Col(Exam.subject_id, "uuid"),
    "created_at": Col(Exam.created_at, "date"),
    "question_count": Col(func.coalesce(_COUNTS.c.n, 0), filterable=False),
    "total_points": Col(func.coalesce(_COUNTS.c.pts, 0), filterable=False),
}


def list_exams(db: Session, scope: OrgScope, params: ListParams):
    stmt = (select(Exam, _COUNTS.c.n, _COUNTS.c.pts).outerjoin(_COUNTS, _COUNTS.c.exam_id == Exam.id)
            .where(Exam.organization_id == scope.org_id, Exam.source != "adaptive"))
    rows, total = paginate(db, stmt, params, EXAM_COLS, search=[Exam.title], scalars=False, default_sort=[Exam.created_at.desc(), Exam.id])
    return [(e, n or 0, float(p or 0)) for e, n, p in rows], total


def create(db: Session, scope: OrgScope, title: str, subject_id=None, grade=None, description: str = "", settings: dict | None = None,
           source: str = "manual") -> Exam:
    if not (title or "").strip():
        raise validation("Nhập tên đề", "title")
    if subject_id:
        s = db.get(Subject, subject_id)
        if s is None or s.organization_id != scope.org_id:
            raise validation("Môn học không hợp lệ", "subject_id")
    e = Exam(organization_id=scope.org_id, title=title.strip(), subject_id=subject_id, grade=grade, description=description or "",
             settings=_settings(settings), created_by=scope.user.id, source=source)
    db.add(e)
    db.flush()
    return e


def _settings(settings: dict | None) -> dict:
    s = {"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10}
    if settings:
        for k, v in (settings.get("points_by_type") or {}).items():
            if k in DEFAULT_POINTS:
                if not isinstance(v, (int, float)) or v <= 0:
                    raise validation("Điểm phải lớn hơn 0", "settings")
                s["points_by_type"][k] = float(v)
        if settings.get("scale_to"):
            s["scale_to"] = float(settings["scale_to"])
    return s


def update(db: Session, scope: OrgScope, exam_id, **changes) -> Exam:
    e = get(db, scope, exam_id)
    if changes.get("title") is not None:
        if not changes["title"].strip():
            raise validation("Nhập tên đề", "title")
        e.title = changes["title"].strip()
    for f in ("description", "grade", "subject_id"):
        if changes.get(f) is not None:
            setattr(e, f, changes[f] or None if f != "description" else changes[f])
    if changes.get("settings") is not None:
        old = e.settings or {}
        e.settings = _settings({**old, **changes["settings"], "points_by_type": {**old.get("points_by_type", {}), **(changes["settings"].get("points_by_type") or {})}})
        # re-apply type defaults to every question of that type
        for eq, qtype in db.execute(select(ExamQuestion, Question.type).join(Question, Question.id == ExamQuestion.question_id).where(ExamQuestion.exam_id == e.id)):
            eq.points = points_for(e, qtype)
    return e


def exam_questions(db: Session, exam: Exam) -> list[tuple[ExamQuestion, Question]]:
    return db.execute(select(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id)
                      .where(ExamQuestion.exam_id == exam.id).order_by(ExamQuestion.position)).all()


EXAM_QUESTION_COLS = {
    "position": Col(ExamQuestion.position, "number"),
    "stem": Col(Question.stem),
    "type": Col(Question.type, "exact"),
    "section": Col(ExamQuestion.section, "exact"),
    "points": Col(ExamQuestion.points, "number"),
}


def question_page(db: Session, scope: OrgScope, exam_id, params: ListParams):
    """One exam's questions as a server-side table (the list only fetches exams)."""
    exam = get(db, scope, exam_id)
    stmt = select(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id).where(ExamQuestion.exam_id == exam.id)
    return paginate(db, stmt, params, EXAM_QUESTION_COLS, search=[Question.stem], scalars=False, default_sort=[ExamQuestion.position])


def _renumber(db: Session, exam: Exam) -> None:
    rows = exam_questions(db, exam)
    rows.sort(key=lambda r: (SECTION_ORDER.index(r[0].section) if r[0].section in SECTION_ORDER else 9, r[0].position))
    for i, (eq, _) in enumerate(rows, start=1):
        eq.position = i
    db.flush()


def _append(db: Session, exam: Exam, q: Question, row: int | None, position: int) -> ExamQuestion:
    eq = ExamQuestion(exam_id=exam.id, question_id=q.id, position=position, section=SECTION_OF_TYPE.get(q.type, "I"),
                      points=points_for(exam, q.type), row=row)
    db.add(eq)
    return eq


def _row_filters(exam: Exam, row: dict) -> dict:
    f = {"status": "usable", "type": row.get("type") or None, "difficulty": row.get("difficulty") or None,
         "topic_id": row.get("topic_id") or None, "tag_ids": [row["tag_id"]] if row.get("tag_id") else None}
    if exam.subject_id:
        f["subject_id"] = exam.subject_id
    return f


def apply_blueprint(db: Session, scope: OrgScope, exam_id, rows: list[dict], seed: int | None = None, replace: bool = True) -> dict:
    exam = get(db, scope, exam_id)
    if _has_attempts(db, exam):
        raise AppError("exam_in_use", "Đề đã có học sinh làm — hãy tạo bản sao để sửa", 409)
    for i, r in enumerate(rows):
        if not isinstance(r.get("count"), int) or not 1 <= r["count"] <= 200:
            raise validation(f"Dòng {i + 1}: số câu từ 1 đến 200", "rows")
        if not (r.get("topic_id") or r.get("tag_id")):
            raise validation(f"Dòng {i + 1}: chọn chuyên đề hoặc tag", "rows")
    if replace:
        db.execute(delete(ExamQuestion).where(ExamQuestion.exam_id == exam.id))
        db.flush()
    rng = random.Random(seed if seed is not None else random.randrange(1 << 30))
    taken = set(db.scalars(select(ExamQuestion.question_id).where(ExamQuestion.exam_id == exam.id)))
    position = len(taken)
    shortfalls, added = [], 0
    for i, row in enumerate(rows):
        pool = [qid for qid in bank.search_ids(db, scope, **_row_filters(exam, row)) if qid not in taken]
        pick = rng.sample(pool, min(row["count"], len(pool)))
        if len(pick) < row["count"]:
            shortfalls.append({"row": i, "missing": row["count"] - len(pick)})
        for qid in pick:
            position += 1
            _append(db, exam, db.get(Question, qid), i, position)
            taken.add(qid)
            added += 1
    exam.blueprint = rows
    exam.source = "blueprint" if exam.source == "manual" else exam.source
    db.flush()
    _renumber(db, exam)
    return {"added": added, "shortfalls": shortfalls}


def _has_attempts(db: Session, exam: Exam) -> bool:
    return bool(db.scalar(select(exists().where(Attempt.exam_id == exam.id))))


def _guard_edit(db: Session, exam: Exam) -> None:
    if _has_attempts(db, exam):
        raise AppError("exam_in_use", "Đề đã có học sinh làm — hãy tạo bản sao để sửa", 409)


def add_questions(db: Session, scope: OrgScope, exam_id, question_ids: list) -> int:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    existing = set(db.scalars(select(ExamQuestion.question_id).where(ExamQuestion.exam_id == exam.id)))
    position = len(existing)
    added = 0
    for qid in question_ids:
        q = db.get(Question, uuid.UUID(str(qid)))
        if q is None or q.organization_id != scope.org_id or q.status not in USABLE:
            raise validation("Chỉ thêm được câu đã duyệt của trung tâm", "question_ids")
        if q.id in existing:
            continue
        position += 1
        _append(db, exam, q, None, position)
        existing.add(q.id)
        added += 1
    db.flush()
    _renumber(db, exam)
    return added


def _part_key(q: Question) -> tuple:
    part = q.part or ""
    return (int(part) if part.isdigit() else 99, part, q.number or 0)


def from_document(db: Session, scope: OrgScope, doc_id, title: str | None = None) -> dict:
    """Draft exam with a document's usable questions in the original PHẦN / Câu order (AC-11, AC-12)."""
    from app.services.documents import get_document

    doc = get_document(db, scope, doc_id)
    if doc.status != "parsed":
        raise validation("Tài liệu chưa tách xong", "document")
    qs = sorted(db.scalars(select(Question).where(Question.source_document_id == doc.id)), key=_part_key)
    usable = [q for q in qs if q.status in USABLE]
    if not usable:
        raise validation("Chưa có câu nào của tài liệu được duyệt — hãy duyệt câu trước", "document")
    meta = doc.meta or {}
    detected = meta.get("detected") or {}
    default_title = " · ".join(x for x in (meta.get("source_name"), meta.get("exam_kind"), meta.get("school_year")) if x)
    stem = doc.filename.rsplit(".", 1)[0]
    exam = create(db, scope, (title or default_title or stem)[:200], subject_id=uuid.UUID(meta["subject_id"]) if meta.get("subject_id") else None,
                  grade=meta.get("grade"), description=f"Tạo từ tài liệu {doc.filename}", source="document")
    exam.settings = {**exam.settings, "source_document_id": str(doc.id), **({"duration_minutes": detected["duration"]} if detected.get("duration") else {})}
    for position, q in enumerate(usable, start=1):
        _append(db, exam, q, None, position)
    db.flush()
    _renumber(db, exam)
    return {"exam_id": exam.id, "added": len(usable), "skipped": len(qs) - len(usable)}


def remove_question(db: Session, scope: OrgScope, exam_id, qid) -> None:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    db.execute(delete(ExamQuestion).where(ExamQuestion.exam_id == exam.id, ExamQuestion.question_id == qid))
    db.flush()
    _renumber(db, exam)


def reorder(db: Session, scope: OrgScope, exam_id, question_ids: list) -> None:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    rows = {eq.question_id: eq for eq, _ in exam_questions(db, exam)}
    ids = [uuid.UUID(str(i)) for i in question_ids]
    if set(ids) != set(rows):
        raise validation("Danh sách câu không khớp đề", "question_ids")
    for i, qid in enumerate(ids, start=1):
        rows[qid].position = i
    db.flush()


def swap(db: Session, scope: OrgScope, exam_id, qid, seed: int | None = None) -> Question:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    eq = db.scalar(select(ExamQuestion).where(ExamQuestion.exam_id == exam.id, ExamQuestion.question_id == qid))
    if eq is None:
        raise not_found("Câu không có trong đề")
    old = db.get(Question, qid)
    row = (exam.blueprint or [])[eq.row] if eq.row is not None and eq.row < len(exam.blueprint or []) else {"type": old.type}
    filters = _row_filters(exam, row) if eq.row is not None else {"status": "usable", "type": old.type, "subject_id": exam.subject_id}
    taken = set(db.scalars(select(ExamQuestion.question_id).where(ExamQuestion.exam_id == exam.id)))
    pool = [i for i in bank.search_ids(db, scope, **filters) if i not in taken]
    if not pool:
        raise AppError("no_replacement", "Không còn câu nào khác phù hợp để đổi", 409)
    new = db.get(Question, random.Random(seed).choice(pool))
    position, section, points, r = eq.position, eq.section, eq.points, eq.row
    db.delete(eq)
    db.flush()
    db.add(ExamQuestion(exam_id=exam.id, question_id=new.id, position=position, section=section, points=points, row=r))
    db.flush()
    return new


def set_points(db: Session, scope: OrgScope, exam_id, qid, points: float) -> None:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    if not isinstance(points, (int, float)) or points <= 0:
        raise validation("Điểm phải lớn hơn 0", "points")
    eq = db.scalar(select(ExamQuestion).where(ExamQuestion.exam_id == exam.id, ExamQuestion.question_id == qid))
    if eq is None:
        raise not_found("Câu không có trong đề")
    eq.points = float(points)


def delete_exam(db: Session, scope: OrgScope, exam_id) -> None:
    exam = get(db, scope, exam_id)
    _guard_edit(db, exam)
    db.delete(exam)


def question_in_use(db: Session, qid) -> bool:
    return bool(db.scalar(select(exists().where(ExamQuestion.question_id == qid))))


if question_in_use not in bank.IN_USE_CHECKS:
    bank.IN_USE_CHECKS.append(question_in_use)
