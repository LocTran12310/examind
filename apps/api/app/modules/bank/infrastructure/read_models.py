"""Bank search, facets and review lists (SQL of subject-scoped-bank and question-review, on the search contract)."""
import uuid

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.bank.application.dto import (
    DocumentRow,
    QuestionView,
    ResolvedFilters,
    ReviewDocumentView,
    TagRefView,
    TopicRefView,
    question_view,
)
from app.modules.bank.domain.entities import STATUS_KEYS, USABLE, Question
from app.modules.bank.domain.services.search_text import query as normalise_query
from app.modules.bank.infrastructure import orm  # noqa: F401  (mapping)
from app.modules.bank.infrastructure.tables import source_documents
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.bank import question_tags, question_topics, questions
from app.shared.infrastructure.schema.identity import users
from app.shared.infrastructure.schema.taxonomy import tags, topics
from app.shared.infrastructure.sql_search import Col, order_by, search, where_clauses

qc, qt, qg, d = questions.c, question_topics.c, question_tags.c, source_documents.c
YEAR = d.metadata["school_year"].astext

QUESTION_COLS = {
    "stem": Col(qc.stem, sortable=False),
    "created_at": Col(qc.created_at, "date"),
    "updated_at": Col(qc.updated_at, "date"),
    "number": Col(qc.number, "number"),
    "grade": Col(qc.grade, "number"),
    "difficulty": Col(qc.difficulty, filterable=False),
    "type": Col(qc.type, filterable=False),
    "confidence": Col(qc.confidence, filterable=False),
}

# the filter dimensions a facet leaves out
_SUBJECT = ("subject_id", "topics", "tags")


def _filtered(org_id: uuid.UUID, rf: ResolvedFilters, drop: tuple[str, ...] = (), base=None):
    """The bank's filter statement (question ids unless `base` says otherwise), without the dimensions in `drop`;
    also the normalised text query."""
    f = rf.filters
    stmt = (base if base is not None else select(qc.id)).where(qc.organization_id == org_id)
    subject_id = None if "subject_id" in drop else f.subject_id
    if subject_id == "none":
        stmt = stmt.where(qc.subject_id.is_(None))
        subject_id = None
    if f.status == "usable":
        stmt = stmt.where(qc.status.in_(USABLE))
    elif f.status and f.status != "all":
        stmt = stmt.where(qc.status == f.status)
    for name, col, val in (("subject_id", qc.subject_id, subject_id), ("grade", qc.grade, f.grade),
                           ("semester_code", qc.semester_code, f.semester_code), ("exam_kind", qc.exam_kind, f.exam_kind),
                           ("type", qc.type, f.type), ("difficulty", qc.difficulty, f.difficulty),
                           ("document_id", qc.source_document_id, f.document_id)):
        if name not in drop and val not in (None, ""):
            stmt = stmt.where(col == val)
    if rf.topic_paths and "topics" not in drop:
        # each chosen node includes its whole subtree; several nodes are OR-ed
        stmt = stmt.where(exists(
            select(qt.question_id).join(topics, topics.c.id == qt.topic_id)
            .where(qt.question_id == qc.id, or_(*[topics.c.path.op("<@")(func.text2ltree(p)) for p in rf.topic_paths]))
        ))
    if rf.tag_groups and "tags" not in drop:
        # any of the chosen tags of one group, and every group (e.g. nguồn đề AND phương pháp)
        for ids in rf.tag_groups:
            stmt = stmt.where(exists(select(qg.question_id).where(qg.question_id == qc.id, qg.tag_id.in_(ids))))
    if f.school_year and "school_year" not in drop:
        stmt = stmt.where(exists(select(d.id).where(d.id == qc.source_document_id, YEAR == f.school_year)))
    needle = normalise_query(f.q) if f.q else ""
    if needle:
        stmt = stmt.where(qc.search_text.contains(needle) | (func.similarity(qc.search_text, needle) > 0.3))
    return stmt, needle


def question_views(session: Session, qs: list[Question], groups: dict | None = None) -> list[QuestionView]:
    """Questions with their topics (primary first) and tags."""
    qids = [q.id for q in qs]
    tops: dict = {qid: [] for qid in qids}
    tgs: dict = {qid: [] for qid in qids}
    if qids:
        for r in session.execute(select(qt.question_id, qt.is_primary, qt.source, qt.score, topics.c.id, topics.c.name)
                                 .join(topics, topics.c.id == qt.topic_id).where(qt.question_id.in_(qids))):
            tops[r.question_id].append(TopicRefView(id=r.id, name=r.name, is_primary=r.is_primary, source=r.source, score=r.score))
        for r in session.execute(select(qg.question_id, tags.c.id, tags.c.group, tags.c.name)
                                 .join(tags, tags.c.id == qg.tag_id).where(qg.question_id.in_(qids))):
            tgs[r.question_id].append(TagRefView(id=r.id, group=r.group, name=r.name))
    return [question_view(q, sorted(tops[q.id], key=lambda t: not t.is_primary), tgs[q.id], (groups or {}).get(q.id)) for q in qs]


class SqlQuestionReader:
    def __init__(self, session: Session):
        self.session = session

    def views(self, questions_: list[Question], groups: dict[uuid.UUID, str] | None = None) -> list[QuestionView]:
        return question_views(self.session, questions_, groups)

    def _where(self, org_id: uuid.UUID, req: SearchRequest, rf: ResolvedFilters, drop: tuple[str, ...] = (), base=None):
        stmt, needle = _filtered(org_id, rf, drop, base)
        for c in where_clauses(QUESTION_COLS, req.filters):
            stmt = stmt.where(c)
        return stmt, needle

    def search(self, org_id: uuid.UUID, req: SearchRequest, rf: ResolvedFilters) -> Page[QuestionView]:
        stmt, needle = self._where(org_id, req, rf, base=select(Question))
        default = [qc.created_at.desc(), qc.number]
        if needle:
            default = [func.similarity(qc.search_text, needle).desc()] + default
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(*order_by(QUESTION_COLS, req, default)).offset(req.offset).limit(req.limit)
        return Page(self.views(list(self.session.scalars(stmt))), total, req.page, req.limit)

    def ids(self, org_id: uuid.UUID, rf: ResolvedFilters) -> list[uuid.UUID]:
        stmt, _ = _filtered(org_id, rf)
        return list(self.session.scalars(stmt.order_by(qc.id)))

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]:
        paths: dict = {}
        tag_ids: dict = {i: [] for i in ids}
        if ids:
            paths = dict(self.session.execute(select(qt.question_id, topics.c.path).join(topics, topics.c.id == qt.topic_id)
                                              .where(qt.question_id.in_(list(ids)), qt.is_primary.is_(True))).all())
            for qid, tid in self.session.execute(select(qg.question_id, qg.tag_id).where(qg.question_id.in_(list(ids)))):
                tag_ids[qid].append(tid)
        return {i: (paths.get(i), tag_ids[i]) for i in ids}

    def demo(self, org_id: uuid.UUID) -> Question | None:
        return self.session.scalar(select(Question).where(qc.organization_id == org_id, qc.source == "demo").limit(1))

    def facets(self, org_id: uuid.UUID, req: SearchRequest, rf: ResolvedFilters) -> dict[str, dict[str, int]]:
        db = self.session

        def sub(*drop: str):
            return self._where(org_id, req, rf, drop)[0].subquery()

        def grouped(col, *drop: str) -> dict:
            s = sub(*drop)
            rows = db.execute(select(col, func.count()).select_from(questions).join(s, s.c.id == qc.id).group_by(col)).all()
            return {("none" if k is None else str(k)): n for k, n in rows}

        out = {
            "subjects": grouped(qc.subject_id, *_SUBJECT),
            "types": grouped(qc.type, "type"),
            "difficulties": grouped(qc.difficulty, "difficulty"),
            "grades": grouped(qc.grade, "grade"),
        }
        s = sub("semester_code", "exam_kind")
        out["periods"] = {f"{sem or ''}|{kind or ''}": n for sem, kind, n in db.execute(
            select(qc.semester_code, qc.exam_kind, func.count()).select_from(questions).join(s, s.c.id == qc.id)
            .where((qc.semester_code.isnot(None)) | (qc.exam_kind.isnot(None)))
            .group_by(qc.semester_code, qc.exam_kind)).all()}
        s = sub("school_year")
        out["school_years"] = {y: n for y, n in db.execute(
            select(YEAR, func.count()).select_from(questions).join(s, s.c.id == qc.id)
            .join(source_documents, d.id == qc.source_document_id).where(YEAR.isnot(None)).group_by(YEAR)).all()}
        s = sub("tags")
        out["tags"] = {str(t): n for t, n in db.execute(
            select(qg.tag_id, func.count()).select_from(question_tags).join(s, s.c.id == qg.question_id).group_by(qg.tag_id)).all()}
        # topics: questions in each node's subtree (a question counted once per node)
        s = sub("topics")
        node, leaf = topics.alias("node"), topics.alias("leaf")
        stmt = (select(node.c.id, func.count(func.distinct(qt.question_id)))
                .select_from(node)
                .join(leaf, leaf.c.path.op("<@")(node.c.path))
                .join(question_topics, qt.topic_id == leaf.c.id)
                .join(s, s.c.id == qt.question_id)
                .where(node.c.organization_id == org_id)
                .group_by(node.c.id))
        subject_id = rf.filters.subject_id
        if subject_id and subject_id != "none":
            stmt = stmt.where(node.c.subject_id == subject_id)
        out["topics"] = {str(t): n for t, n in db.execute(stmt).all()}
        return out


# ------------------------------------------------------------------ review lists

_TOTAL = func.count(qc.id)
REVIEW_DOC_COLS = {
    "filename": Col(d.filename),
    "source_name": Col(d.metadata["source_name"].astext),
    "assigned_to": Col(d.assigned_to, "uuid"),
    "created_at": Col(d.created_at, "date"),
    "total": Col(_TOTAL, filterable=False),
    "needs_review": Col(func.count(case((qc.status == "needs_review", 1))), filterable=False),
}
FLAGGED_COLS = {"stem": Col(qc.stem), "updated_at": Col(qc.updated_at, "date")}


def _counts_stmt(org_id: uuid.UUID):
    cols = [func.count(case((qc.status == s, 1))).label(s) for s in STATUS_KEYS]
    spot = func.count(case((and_(qc.spot_check.is_(True), qc.status == "auto_approved"), 1))).label("spot_pending")
    return (select(source_documents, _TOTAL.label("total"), *cols, spot)
            .select_from(source_documents)
            .outerjoin(questions, qc.source_document_id == d.id)
            .where(d.organization_id == org_id, d.status == "parsed")
            .group_by(d.id))


class SqlReviewReader:
    def __init__(self, session: Session):
        self.session = session

    def search_documents(self, org_id: uuid.UUID, req: SearchRequest, assigned_to: uuid.UUID | None = None) -> Page[ReviewDocumentView]:
        stmt = _counts_stmt(org_id)
        if assigned_to is not None:
            stmt = stmt.where(d.assigned_to == assigned_to)
        rows, total = search(self.session, stmt, req, REVIEW_DOC_COLS, text=[d.filename, d.metadata["source_name"].astext],
                             default_sort=[d.created_at.desc(), d.id], scalars=False)
        return Page(self._out(rows), total, req.page, req.limit)

    def document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> ReviewDocumentView | None:
        rows = self._out(self.session.execute(_counts_stmt(org_id).where(d.id == document_id)).all())
        return rows[0] if rows else None

    def flagged(self, org_id: uuid.UUID, req: SearchRequest) -> Page[Question]:
        stmt = select(Question).where(qc.organization_id == org_id, qc.status == "flagged")
        rows, total = search(self.session, stmt, req, FLAGGED_COLS, text=[qc.stem], default_sort=[qc.updated_at.desc().nulls_last(), qc.id])
        return Page(list(rows), total, req.page, req.limit)

    def _out(self, rows) -> list[ReviewDocumentView]:
        assignees = {r.assigned_to for r in rows if r.assigned_to}
        names = dict(self.session.execute(select(users.c.id, users.c.full_name).where(users.c.id.in_(assignees))).all()) if assignees else {}
        out = []
        for r in rows:
            counts = {s: getattr(r, s) for s in STATUS_KEYS}
            done = counts["approved"] + counts["rejected"] + counts["duplicate"] + counts["auto_approved"] - r.spot_pending
            doc = DocumentRow(id=r.id, filename=r.filename, mime=r.mime, size=r.size, status=r.status, error=r.error, meta=r.metadata or {},
                              processing_config=r.processing_config or {}, page_count=r.page_count, question_count=r.question_count,
                              log=r.log or [], created_at=r.created_at, finished_at=r.finished_at)
            out.append(ReviewDocumentView(document=doc, total=r.total, counts=counts, spot_pending=r.spot_pending,
                                          progress=round(done / r.total, 2) if r.total else 1.0,
                                          assigned_to=r.assigned_to, assigned_name=names.get(r.assigned_to)))
        return out
