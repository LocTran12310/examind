"""Taxonomy seen from ingestion: subjects, semesters and topics are read through SQLAlchemy Core (ADR-01: read models may
read any table); the source tag, a write, goes through the taxonomy context's application API, handed in by the
composition root (ingestion never imports another module)."""
from typing import Protocol
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ingestion.domain.ports import TopicNode
from app.shared.infrastructure.schema.taxonomy import semesters, subjects, topics


class _SourceTags(Protocol):
    def source_tag(self, org_id: uuid.UUID, name: str) -> uuid.UUID: ...


s, se, t = subjects.c, semesters.c, topics.c


class SqlTaxonomyLookup:
    def __init__(self, session: Session, tags: _SourceTags | None = None):
        self.session, self.tags = session, tags

    def subjects(self, org_id: uuid.UUID) -> list[tuple[uuid.UUID, str, str]]:
        return [tuple(r) for r in self.session.execute(select(s.id, s.name, s.code).where(s.organization_id == org_id))]

    def subject_in_org(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self.session.scalar(select(s.id).where(s.id == subject_id, s.organization_id == org_id)) is not None

    def semester_codes(self, org_id: uuid.UUID) -> set[str]:
        return set(self.session.scalars(select(se.code).where(se.organization_id == org_id)))

    def subject_id_by_code(self, org_id: uuid.UUID, code: str) -> uuid.UUID | None:
        return self.session.scalar(select(s.id).where(s.organization_id == org_id, s.code == code))

    def topics(self, org_id: uuid.UUID, subject_id) -> list[TopicNode]:
        sid = uuid.UUID(str(subject_id)) if subject_id else None
        stmt = select(t.id, t.name, t.path, t.parent_id).where(t.organization_id == org_id, t.subject_id == sid).order_by(t.path)
        return [TopicNode(*r) for r in self.session.execute(stmt)]

    def topic(self, topic_id: uuid.UUID) -> TopicNode | None:
        r = self.session.execute(select(t.id, t.name, t.path, t.parent_id).where(t.id == topic_id)).first()
        return TopicNode(*r) if r else None

    def source_tag(self, org_id: uuid.UUID, name: str | None) -> uuid.UUID | None:
        if not name:
            return None
        if self.tags is None:
            raise RuntimeError("no taxonomy registered")
        return self.tags.source_tag(org_id, name)
