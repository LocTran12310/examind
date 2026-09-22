import uuid

from sqlalchemy import delete, exists, insert, select, text, update
from sqlalchemy.orm import Session

from app.modules.bank.domain.entities import USABLE, Question, ReviewEvent
from app.modules.bank.infrastructure import orm  # noqa: F401  (mapping)
from app.modules.bank.infrastructure.tables import exam_questions
from app.shared.infrastructure.schema.bank import question_tags, question_topics, questions, review_events

qc = questions.c


def release_duplicates_of(session: Session, gone) -> None:
    """Before questions are deleted: copies marked "duplicate" of them go back to review.
    `gone` selects the question ids (a list or a SELECT); the old layout's re-parse passes a SELECT."""
    session.execute(update(questions).where(qc.duplicate_of.in_(gone), qc.status == "duplicate")
                    .values(status="needs_review", duplicate_of=None).execution_options(synchronize_session=False))


class SqlQuestionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID, question_id: uuid.UUID) -> Question | None:
        q = self.session.get(Question, question_id)
        return q if q is not None and q.organization_id == org_id else None

    def many(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list[Question]:
        if not ids:
            return []
        stmt = select(Question).where(qc.id.in_(ids))
        if org_id is not None:
            stmt = stmt.where(qc.organization_id == org_id)
        return list(self.session.scalars(stmt))

    def review_queue(self, document_id: uuid.UUID) -> list[Question]:
        return list(self.session.scalars(select(Question).where(
            qc.source_document_id == document_id,
            qc.status.in_(("needs_review", "flagged")) | (qc.spot_check.is_(True) & (qc.status == "auto_approved")),
        )))

    def of_document(self, document_id: uuid.UUID, *, type: str | None = None, status: str | None = None,
                    spot_check: bool | None = None) -> list[Question]:
        stmt = select(Question).where(qc.source_document_id == document_id)
        if type is not None:
            stmt = stmt.where(qc.type == type)
        if status is not None:
            stmt = stmt.where(qc.status == status)
        if spot_check is not None:
            stmt = stmt.where(qc.spot_check.is_(spot_check))
        return list(self.session.scalars(stmt))

    def add(self, q: Question) -> None:
        self.session.add(q)
        self.session.flush()

    def remove(self, q: Question) -> None:
        self.session.flush()
        self.session.delete(q)
        self.session.flush()

    def release_duplicates_of(self, question_ids: list[uuid.UUID]) -> None:
        release_duplicates_of(self.session, list(question_ids))

    def replace_topics(self, question_id: uuid.UUID, topic_ids: list[uuid.UUID], primary_id: uuid.UUID | None) -> None:
        self.session.flush()
        self.session.execute(delete(question_topics).where(question_topics.c.question_id == question_id))
        if topic_ids:
            self.session.execute(insert(question_topics), [
                {"question_id": question_id, "topic_id": t, "is_primary": t == primary_id, "source": "manual", "score": 1.0} for t in topic_ids])

    def tag_ids(self, question_id: uuid.UUID) -> set[uuid.UUID]:
        return set(self.session.scalars(select(question_tags.c.tag_id).where(question_tags.c.question_id == question_id)))

    def replace_tags(self, question_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None:
        self.session.flush()
        self.session.execute(delete(question_tags).where(question_tags.c.question_id == question_id))
        if tag_ids:
            self.session.execute(insert(question_tags), [{"question_id": question_id, "tag_id": t} for t in tag_ids])


class SqlReviewLog:
    def __init__(self, session: Session):
        self.session = session

    def record(self, org_id: uuid.UUID, user_id: uuid.UUID | None, question_id: uuid.UUID | None, action: str,
               before: dict | None, after: dict | None) -> None:
        self.session.add(ReviewEvent(organization_id=org_id, question_id=question_id, user_id=user_id, action=action,
                                     before=before, after=after))

    def recent_spot_actions(self, org_id: uuid.UUID, limit: int) -> list[str]:
        self.session.flush()
        e = review_events.c
        return list(self.session.scalars(select(e.action).where(e.organization_id == org_id, e.action.in_(("spot_ok", "spot_fail")))
                                         .order_by(e.created_at.desc()).limit(limit)))


class SqlDuplicateFinder:
    """Trigram similarity on search_text (pg_trgm `%`)."""

    def __init__(self, session: Session):
        self.session = session

    def similar(self, q: Question, limit: int = 5) -> list[tuple[uuid.UUID, float, str]]:
        rows = self.session.execute(text("""
            select id, similarity(search_text, :t) as s, search_text from questions
             where organization_id = :o and status = any(:usable) and type = :type and id <> :id
               and (cast(:doc as uuid) is null or source_document_id is distinct from cast(:doc as uuid)) and search_text % :t
             order by s desc,
                      -- equal similarity (the same text twice in a file): the question at the same place wins, then the oldest
                      (number is distinct from cast(:number as integer) or part is distinct from cast(:part as varchar)),
                      created_at, id
             limit :n"""),
            {"t": q.search_text, "o": q.organization_id, "usable": list(USABLE), "type": q.type, "id": q.id,
             "doc": q.source_document_id, "number": q.number, "part": q.part, "n": limit}).all()
        return [(r.id, r.s, r.search_text) for r in rows]


class SqlDocumentQuestions:
    def __init__(self, session: Session):
        self.session = session

    def in_order(self, document_id: uuid.UUID) -> list[Question]:
        return list(self.session.scalars(select(Question).where(qc.source_document_id == document_id)
                                         .order_by(qc.part.nulls_first(), qc.number)))

    def remove(self, document_id: uuid.UUID, keep_statuses: tuple[str, ...], keep_used: bool) -> None:
        gone = [qc.source_document_id == document_id, qc.status.notin_(keep_statuses)]
        if keep_used:
            gone.append(~exists(select(exam_questions.c.question_id).where(exam_questions.c.question_id == qc.id)))
        self.session.flush()
        release_duplicates_of(self.session, select(qc.id).where(*gone))
        self.session.execute(delete(Question).where(*gone))

    def positions(self, document_id: uuid.UUID) -> set[tuple[str | None, int | None]]:
        return {(q.part, q.number) for q in self.session.scalars(select(Question).where(qc.source_document_id == document_id))}

    def add_all(self, qs: list[Question], tag_id: uuid.UUID | None) -> None:
        self.session.add_all(qs)
        self.session.flush()
        if tag_id and qs:
            self.session.execute(insert(question_tags), [{"question_id": q.id, "tag_id": tag_id} for q in qs])
        self.session.flush()

    def nearest_topic(self, q: Question) -> tuple[uuid.UUID, float] | None:
        if not q.search_text:
            return None
        row = self.session.execute(text("""
            select qt.topic_id, similarity(o.search_text, :t) as s
              from questions o join question_topics qt on qt.question_id = o.id and qt.is_primary
             where o.organization_id = :org and o.status = 'approved' and o.id <> :id and o.search_text % :t
             order by s desc limit 1"""), {"t": q.search_text, "org": q.organization_id, "id": q.id}).first()
        return (row[0], float(row[1])) if row else None

    def add_topic(self, question_id: uuid.UUID, topic_id: uuid.UUID, is_primary: bool, source: str, score: float | None) -> None:
        self.session.execute(insert(question_topics).values(question_id=question_id, topic_id=topic_id, is_primary=is_primary,
                                                            source=source, score=score))

    def swap_tag(self, question_ids: list[uuid.UUID], old_tag_id: uuid.UUID | None, new_tag_id: uuid.UUID | None) -> None:
        self.session.flush()
        if old_tag_id and question_ids:
            self.session.execute(delete(question_tags).where(question_tags.c.tag_id == old_tag_id, question_tags.c.question_id.in_(question_ids)))
        if new_tag_id and question_ids:
            self.session.execute(insert(question_tags), [{"question_id": qid, "tag_id": new_tag_id} for qid in question_ids])


# Other contexts register what still uses a question (fn(session, question_id) -> bool), e.g. exams.
IN_USE_CHECKS: list = []


class SqlQuestionUsage:
    def __init__(self, session: Session):
        self.session = session

    def in_use(self, question_id: uuid.UUID) -> bool:
        return any(check(self.session, question_id) for check in IN_USE_CHECKS)

