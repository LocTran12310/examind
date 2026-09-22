"""Mastery rows (ORM on the dataclass) and what a plan reads: topics (taxonomy tables), the graded answer facts
(assessment's table) and the usable questions of the bank (SQLAlchemy Core / SQL, ADR-01)."""
from collections.abc import Iterable
from datetime import datetime
import uuid

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.value_objects import USABLE, AnswerRecord, TopicNode
from app.modules.analytics.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.schema.analytics import student_topic_mastery
from app.shared.infrastructure.schema.assessment import answer_facts
from app.shared.infrastructure.schema.taxonomy import topics

m_c, t_c, f_c = student_topic_mastery.c, topics.c, answer_facts.c
_TOPIC = (t_c.id, t_c.parent_id, t_c.name, t_c.path, t_c.subject_id)


def _node(r) -> TopicNode:
    return TopicNode(r.id, r.parent_id, r.name, r.path, r.subject_id)


class SqlMasteryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, student_id: uuid.UUID, topic_id: uuid.UUID) -> TopicMastery | None:
        return self.session.get(TopicMastery, (student_id, topic_id))

    def add(self, row: TopicMastery) -> None:
        self.session.add(row)

    def leaves(self, org_id: uuid.UUID, student_id: uuid.UUID) -> list[tuple[TopicMastery, TopicNode]]:
        rows = self.session.execute(select(TopicMastery, *_TOPIC).join(topics, t_c.id == m_c.topic_id)
                                    .where(m_c.student_id == student_id, m_c.organization_id == org_id)).all()
        return [(r[0], _node(r)) for r in rows]

    def clear(self, org_id: uuid.UUID | None) -> None:
        stmt = delete(TopicMastery)
        if org_id:
            stmt = stmt.where(TopicMastery.organization_id == org_id)
        self.session.execute(stmt)

    def empty(self) -> bool:
        return self.session.scalar(select(m_c.student_id).limit(1)) is None

    def flush(self) -> None:
        self.session.flush()


class SqlTopics:
    def __init__(self, session: Session):
        self.session = session

    def id_by_path(self, org_id: uuid.UUID, path: str) -> uuid.UUID | None:
        return self.session.scalar(select(t_c.id).where(t_c.organization_id == org_id, t_c.path == path))

    def of_org(self, org_id: uuid.UUID) -> dict[uuid.UUID, TopicNode]:
        return {r.id: _node(r) for r in self.session.execute(select(*_TOPIC).where(t_c.organization_id == org_id))}

    def get(self, topic_id: uuid.UUID) -> TopicNode | None:
        r = self.session.execute(select(*_TOPIC).where(t_c.id == topic_id)).first()
        return _node(r) if r else None

    def strands(self, org_id: uuid.UUID, subject_id: uuid.UUID | None) -> list[TopicNode]:
        stmt = select(*_TOPIC).where(t_c.organization_id == org_id, t_c.parent_id.is_(None))
        if subject_id:
            stmt = stmt.where(t_c.subject_id == subject_id)
        return [_node(r) for r in self.session.execute(stmt)]


class SqlAnswerHistory:
    def __init__(self, session: Session):
        self.session = session

    def recent_correct(self, org_id: uuid.UUID, student_id: uuid.UUID, since: datetime) -> set[uuid.UUID]:
        return set(self.session.scalars(text("""select question_id from answer_facts where organization_id=:o and student_id=:s
                                                and correct_ratio >= 1 and created_at > :since"""),
                                        {"o": org_id, "s": student_id, "since": since}))

    def mistakes_to_reask(self, org_id: uuid.UUID, student_id: uuid.UUID, before: datetime, limit: int) -> list[uuid.UUID]:
        return list(self.session.scalars(text("""
            select f.question_id from answer_facts f join questions q on q.id = f.question_id and q.status = any(:usable)
             where f.organization_id=:o and f.student_id=:s and f.correct_ratio < 1 and f.created_at < :cut
               and not exists (select 1 from answer_facts g where g.student_id=f.student_id and g.question_id=f.question_id
                               and g.correct_ratio >= 1 and g.created_at > f.created_at)
             group by f.question_id order by max(f.created_at) desc limit :n"""),
            {"o": org_id, "s": student_id, "cut": before, "usable": list(USABLE), "n": limit}))

    def replay(self, org_id: uuid.UUID | None) -> Iterable[AnswerRecord]:
        stmt = select(f_c.organization_id, f_c.student_id, f_c.topic_path, f_c.correct_ratio, f_c.difficulty, f_c.created_at
                      ).order_by(f_c.created_at, f_c.id)
        if org_id:
            stmt = stmt.where(f_c.organization_id == org_id)
        return [AnswerRecord(*r) for r in self.session.execute(stmt).all()]

    def empty(self) -> bool:
        return self.session.scalar(select(f_c.id).limit(1)) is None


class SqlQuestionPool:
    def __init__(self, session: Session):
        self.session = session

    def pool(self, org_id: uuid.UUID, topic_path: str | None, exclude: set, subject_id: uuid.UUID | None = None) -> list[tuple[uuid.UUID, str | None]]:
        params = {"o": org_id, "usable": list(USABLE)}
        where = ["q.organization_id = :o", "q.status = any(:usable)"]
        if topic_path:
            where.append("exists (select 1 from question_topics qt join topics t on t.id = qt.topic_id "
                         "where qt.question_id = q.id and t.path <@ cast(:p as ltree))")
            params["p"] = topic_path
        if subject_id:
            where.append("q.subject_id = :s")
            params["s"] = subject_id
        rows = self.session.execute(text(f"select q.id, q.difficulty from questions q where {' and '.join(where)}"), params).all()
        return [(r[0], r[1]) for r in rows if r[0] not in exclude]
