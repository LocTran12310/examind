"""Bank search, facets, review lists and item statistics (SQL of subject-scoped-bank, question-review and
learning-telemetry, on the search contract)."""
import uuid

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.bank.application.dto import (
    DocumentRow,
    EventBatchView,
    ItemStats,
    OptionStat,
    QuestionView,
    ResolvedFilters,
    ReviewDocumentView,
    TagRefView,
    TopicRefView,
    question_view,
)
from app.modules.bank.domain.entities import SNAPSHOT_FIELDS, STATUS_KEYS, STATUSES, USABLE, Question
from app.modules.bank.domain.services.history import BLOCKED, UNDONE_BATCH, batch_action, changed_fields, undo_block
from app.modules.bank.domain.services.review import REVIEW_STATES, WAITING, pending_count, review_state
from app.modules.bank.domain.services.search_text import query as normalise_query
from app.modules.bank.infrastructure import orm  # noqa: F401  (mapping)
from app.modules.bank.infrastructure.tables import answer_facts, attempt_answers, attempts, source_documents
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.clock import utcnow
from app.shared.infrastructure.schema.bank import question_tags, question_topics, questions, review_events
from app.shared.infrastructure.schema.identity import users
from app.shared.infrastructure.schema.taxonomy import tags, topics
from app.shared.infrastructure.sql_search import Col, order_by, search, where_clauses

qc, qt, qg, d = questions.c, question_topics.c, question_tags.c, source_documents.c
ev = review_events.c
af, att, ans = answer_facts.c, attempts.c, attempt_answers.c
YEAR = d.metadata["school_year"].astext
# the item statistics the bank can be searched by (learning-telemetry AC-04); joined only when a request names one
STATS_FIELDS = ("stats_observations", "stats_correct_ratio")

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
    if f.has_topic is not None and "topics" not in drop:
        # the tagging queue: `false` is "no row in question_topics at all", not "not in these nodes"
        placed = exists(select(qt.question_id).where(qt.question_id == qc.id))
        stmt = stmt.where(placed if f.has_topic else ~placed)
    if f.school_year and "school_year" not in drop:
        stmt = stmt.where(exists(select(d.id).where(d.id == qc.source_document_id, YEAR == f.school_year)))
    needle = normalise_query(f.q) if f.q else ""
    if needle:
        stmt = stmt.where(qc.search_text.contains(needle) | (func.similarity(qc.search_text, needle) > 0.3))
    return stmt, needle


def _stats_sub(org_id: uuid.UUID):
    """Observations and mean correct ratio per question in one grouped pass over the facts (never a query per row)."""
    return (select(af.question_id.label("question_id"), func.count().label("observations"),
                   func.avg(af.correct_ratio).label("correct_ratio"))
            .where(af.organization_id == org_id).group_by(af.question_id).subquery("item_stats"))


def _with_stats(stmt, org_id: uuid.UUID, req: SearchRequest):
    """The statement and the columns to read it by: the aggregate is joined only when the request filters or sorts
    on one of the statistics."""
    if not (set(req.filters) & set(STATS_FIELDS) or any(k.field in STATS_FIELDS for k in req.sort)):
        return stmt, QUESTION_COLS
    s = _stats_sub(org_id)
    cols = {**QUESTION_COLS,
            "stats_observations": Col(func.coalesce(s.c.observations, 0), "number"),
            "stats_correct_ratio": Col(s.c.correct_ratio, "number")}
    return stmt.outerjoin(s, s.c.question_id == qc.id), cols


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
        stmt, cols = _with_stats(stmt, org_id, req)
        for c in where_clauses(cols, req.filters):
            stmt = stmt.where(c)
        return stmt, needle, cols

    def search(self, org_id: uuid.UUID, req: SearchRequest, rf: ResolvedFilters) -> Page[QuestionView]:
        stmt, needle, cols = self._where(org_id, req, rf, base=select(Question))
        default = [qc.created_at.desc(), qc.number]
        if needle:
            default = [func.similarity(qc.search_text, needle).desc()] + default
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(*order_by(cols, req, default)).offset(req.offset).limit(req.limit)
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
        # questions nobody tagged with a topic: they answer no report and move no mastery, so the gap is countable
        s = sub("topics")
        no_topic = ~exists().where(qt.question_id == qc.id)
        untagged = db.scalar(select(func.count()).select_from(questions).join(s, s.c.id == qc.id).where(no_topic))
        if untagged:
            out["topics"]["none"] = untagged
        # the same gap paper by paper, so a teacher can clear one document at a time (topic-coverage AC-05)
        s = sub("topics", "document_id")
        out["untagged_documents"] = {("none" if doc is None else str(doc)): n for doc, n in db.execute(
            select(qc.source_document_id, func.count()).select_from(questions).join(s, s.c.id == qc.id)
            .where(no_topic).group_by(qc.source_document_id)).all()}
        return out


# ------------------------------------------------------------------ item statistics (learning-telemetry ADR-03)

BANDS = 3  # discrimination compares the strongest third of the attempts with the weakest


def _score_ratio():
    """What the attempt scored, 0..1 (no maximum: 0) — the ranking the discrimination and the key audit share."""
    return case((att.max_score > 0, func.coalesce(att.score, 0) / att.max_score), else_=0.0)


def _rounded(value) -> float | None:
    return None if value is None else round(float(value), 3)


class SqlItemStatsReader:
    """What the graded answers say about a question, aggregated in SQL: the question detail, and the answers the key
    audit judges (the same facts, the same score ranking)."""

    def __init__(self, session: Session):
        self.session = session

    def stats(self, org_id: uuid.UUID, q: Question) -> ItemStats:
        band = func.ntile(BANDS).over(order_by=(_score_ratio().desc(), af.attempt_id))
        facts = (select(af.correct_ratio.label("correct"), af.first_attempt.label("first"), af.seconds_spent.label("seconds"),
                        band.label("band"))
                 .select_from(answer_facts).join(attempts, att.id == af.attempt_id)
                 .where(af.organization_id == org_id, af.question_id == q.id)).subquery()
        f = facts.c
        r = self.session.execute(select(
            func.count().label("observations"),
            func.avg(f.correct).label("correct_ratio"),
            func.avg(case((f.first.is_(True), f.correct))).label("first_attempt_ratio"),
            func.avg(case((f.band == 1, f.correct))).label("top"),
            func.avg(case((f.band == BANDS, f.correct))).label("bottom"),
            func.percentile_cont(0.5).within_group(f.seconds).label("median_seconds"),
        )).one()
        top, bottom = _rounded(r.top), _rounded(r.bottom)
        return ItemStats(
            observations=r.observations, correct_ratio=_rounded(r.correct_ratio), first_attempt_ratio=_rounded(r.first_attempt_ratio),
            discrimination=None if top is None or bottom is None else round(top - bottom, 3),
            median_seconds=None if r.median_seconds is None else round(r.median_seconds),
            options=self._options(org_id, q, r.observations) if q.type == "mcq" else [],
        )

    def _options(self, org_id: uuid.UUID, q: Question, observations: int) -> list[OptionStat]:
        """How many of those answers chose each option: the responses are stored in the question's own labels."""
        label = ans.response["key"].astext
        chosen = dict(self.session.execute(
            select(label, func.count()).select_from(answer_facts)
            .join(attempt_answers, and_(ans.attempt_id == af.attempt_id, ans.question_id == af.question_id))
            .where(af.organization_id == org_id, af.question_id == q.id).group_by(label)).all())
        key = (q.answer or {}).get("key")
        return [OptionStat(label=o["label"], chosen=chosen.get(o["label"], 0),
                           ratio=round(chosen.get(o["label"], 0) / observations, 3) if observations else 0.0,
                           is_key=o["label"] == key)
                for o in q.options or []]

    def mcq_answers(self, org_id: uuid.UUID | None) -> dict[uuid.UUID, list[tuple[dict | None, float]]]:
        """{question_id: [(response, the attempt's score ratio)]} of the usable MCQs — what the key audit weighs."""
        stmt = (select(ans.question_id, ans.response, _score_ratio()).select_from(attempt_answers)
                .join(attempts, att.id == ans.attempt_id).join(questions, qc.id == ans.question_id)
                .where(att.status == "submitted", qc.type == "mcq", qc.status.in_(USABLE), ans.points.is_not(None)))
        if org_id:
            stmt = stmt.where(qc.organization_id == org_id)
        out: dict = {}
        for qid, response, ratio in self.session.execute(stmt):
            out.setdefault(qid, []).append((response, float(ratio)))
        return out


# ------------------------------------------------------------------ review lists

_TOTAL = func.count(qc.id)
FLAGGED_COLS = {"stem": Col(qc.stem), "updated_at": Col(qc.updated_at, "date")}
# what still waits for a human, in SQL: the `waits_for_review` rule of the domain, question by question
_WAITING = or_(qc.status.in_(WAITING), and_(qc.spot_check.is_(True), qc.status == "auto_approved"))
_STATE_CLAUSES = {
    "pending": _WAITING,
    "approved": and_(qc.status.in_(("approved", "auto_approved")), ~_WAITING),
    "rejected": qc.status == "rejected",
    "duplicate": qc.status == "duplicate",
}
DOC_QUESTION_COLS = {
    "stem": Col(qc.stem, sortable=False),
    "number": Col(qc.number, "number"),
    "created_at": Col(qc.created_at, "date"),
    "updated_at": Col(qc.updated_at, "date"),
    "status": Col(qc.status, "enum", values=STATUSES),
}


def _counts(org_id: uuid.UUID):
    """One row per parsed document with its review counts. A subquery, so the counts the state is derived from are
    ordinary columns the search contract can filter and sort by (ADR-01)."""
    cols = [func.count(case((qc.status == s, 1))).label(s) for s in STATUS_KEYS]
    spot = func.count(case((and_(qc.spot_check.is_(True), qc.status == "auto_approved"), 1))).label("spot_pending")
    return (select(source_documents, _TOTAL.label("total"), *cols, spot)
            .select_from(source_documents)
            .outerjoin(questions, qc.source_document_id == d.id)
            .where(d.organization_id == org_id, d.status == "parsed")
            .group_by(d.id)).subquery("review_documents")


def _review_doc_cols(s) -> dict[str, Col]:
    """The review list's columns over `_counts`: `pending` and `review_state` mirror the domain rules of the same
    name so a filter and a row say the same thing; the breakdown stays in the row."""
    c = s.c
    pending = c.needs_review + c.flagged + c.spot_pending
    decided = c.approved + c.rejected + c.duplicate + c.auto_approved - c.spot_pending
    return {
        "filename": Col(c.filename),
        "source_name": Col(c.metadata["source_name"].astext),
        "assigned_to": Col(c.assigned_to, "uuid"),
        "created_at": Col(c.created_at, "date"),
        "total": Col(c.total, filterable=False),
        "needs_review": Col(c.needs_review, filterable=False),
        "pending": Col(pending, "number"),
        # the same ratio the row draws as a bar, as an expression the sort can order by. A document with no
        # question at all reads 1.0 here exactly as `_out` reports it — the two must not disagree, or the list
        # would sort by a number nobody can see. Not filterable: "documents above 80%" is not a question anyone
        # asks, and a float filter on a ratio invites 0.9499 problems.
        "progress": Col(case((c.total > 0, decided * 1.0 / c.total), else_=1.0), "number", filterable=False),
        "review_state": Col(case((pending > 0, "pending"), (decided >= c.total, "done"), else_="in_progress"),
                            "enum", values=REVIEW_STATES),
    }


class SqlReviewReader:
    def __init__(self, session: Session):
        self.session = session

    def search_documents(self, org_id: uuid.UUID, req: SearchRequest, assigned_to: uuid.UUID | None = None) -> Page[ReviewDocumentView]:
        s = _counts(org_id)
        stmt = select(s)
        if assigned_to is not None:
            stmt = stmt.where(s.c.assigned_to == assigned_to)
        rows, total = search(self.session, stmt, req, _review_doc_cols(s),
                             text=[s.c.filename, s.c.metadata["source_name"].astext],
                             default_sort=[s.c.created_at.desc(), s.c.id], scalars=False)
        return Page(self._out(rows), total, req.page, req.limit)

    def document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> ReviewDocumentView | None:
        s = _counts(org_id)
        rows = self._out(self.session.execute(select(s).where(s.c.id == document_id)).all())
        return rows[0] if rows else None

    def document_questions(self, org_id: uuid.UUID, document_id: uuid.UUID, state: str, req: SearchRequest) -> Page[Question]:
        stmt = select(Question).where(qc.organization_id == org_id, qc.source_document_id == document_id)
        clause = _STATE_CLAUSES.get(state)
        if clause is not None:
            stmt = stmt.where(clause)
        rows, total = search(self.session, stmt, req, DOC_QUESTION_COLS, text=[qc.stem],
                             default_sort=[qc.part.nulls_first(), qc.number.nulls_last(), qc.id])
        return Page(list(rows), total, req.page, req.limit)

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
                                          pending=pending_count(counts, r.spot_pending),
                                          review_state=review_state(r.total, counts, r.spot_pending),
                                          progress=round(done / r.total, 2) if r.total else 1.0,
                                          assigned_to=r.assigned_to, assigned_name=names.get(r.assigned_to)))
        return out



class SqlEventReader:
    """The review history grouped by the request that wrote it (bulk-safety ADR-01). An event from before the batch
    column stands alone — a batch cannot be reconstructed from a timestamp, so it is a group of one that says so.
    The grouping is a subquery: over it every column is an ordinary one, so the list filters and sorts like the rest."""

    def __init__(self, session: Session):
        self.session = session

    def batches(self, org_id: uuid.UUID, req: SearchRequest) -> Page[EventBatchView]:
        key = func.coalesce(ev.batch_id, ev.id)
        grouped = (select(key.label("batch_key"), ev.batch_id.label("batch_id"), ev.user_id.label("user_id"),
                          func.min(ev.created_at).label("created_at"),
                          func.count(func.distinct(ev.question_id)).label("questions"))
                   .where(ev.organization_id == org_id)
                   # the actor and the batch are the same on every event of one request, so grouping by them costs
                   # nothing and spares an aggregate over uuid, which Postgres has no max() for
                   .group_by(key, ev.batch_id, ev.user_id).subquery())
        b = grouped.c
        cols = {"created_at": Col(b.created_at, "date"), "user_id": Col(b.user_id, "uuid", sortable=False),
                "questions": Col(b.questions, "number")}
        stmt = (select(b.batch_key, b.batch_id, b.user_id, b.created_at, b.questions, users.c.full_name)
                .select_from(grouped).outerjoin(users, users.c.id == b.user_id))
        rows, total = search(self.session, stmt, req, cols, default_sort=[b.created_at.desc(), b.batch_key], scalars=False)
        if not rows:
            return Page([], total, req.page, req.limit)
        actions, fields = self._detail(org_id, [r.batch_key for r in rows])
        undone = self._undone(org_id, [r.batch_id for r in rows if r.batch_id])
        now = utcnow()
        out = []
        for r in rows:
            action = batch_action(actions.get(r.batch_key, ()))
            blocked = undo_block(r.batch_id is not None, action, r.created_at, now, str(r.batch_id) in undone)
            out.append(EventBatchView(batch_id=r.batch_id, created_at=r.created_at, user_id=r.user_id, actor_name=r.full_name,
                                      action=action, fields=sorted(fields.get(r.batch_key, ()), key=SNAPSHOT_FIELDS.index),
                                      questions=r.questions, undoable=blocked is None, reason=blocked,
                                      message=BLOCKED.get(blocked) if blocked else None))
        return Page(out, total, req.page, req.limit)

    def _detail(self, org_id: uuid.UUID, keys: list[uuid.UUID]) -> tuple[dict, dict]:
        """What each batch of the page did: the actions it recorded and the snapshot fields it moved."""
        rows = self.session.execute(select(func.coalesce(ev.batch_id, ev.id).label("batch_key"), ev.action, ev.before, ev.after)
                                    .where(ev.organization_id == org_id, func.coalesce(ev.batch_id, ev.id).in_(keys))).all()
        actions: dict[uuid.UUID, set] = {}
        fields: dict[uuid.UUID, set] = {}
        for r in rows:
            actions.setdefault(r.batch_key, set()).add(r.action)
            fields.setdefault(r.batch_key, set()).update(changed_fields(r.before, r.after))
        return actions, fields

    def _undone(self, org_id: uuid.UUID, batch_ids: list[uuid.UUID]) -> set[str]:
        """Which of these batches an `undo` has already reversed (A-04); the undo names its batch in its own event."""
        undone = ev.after[UNDONE_BATCH].astext
        return set(self.session.scalars(select(undone).where(ev.organization_id == org_id, ev.action == "undo",
                                                             undone.in_([str(b) for b in batch_ids])))) if batch_ids else set()
