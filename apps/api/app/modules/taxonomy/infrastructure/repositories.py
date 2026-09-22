import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.schema.taxonomy import tags


class SqlTagRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None:
        tag = self.session.get(Tag, tag_id)
        return tag if tag is not None and tag.organization_id == org_id else None

    def name_taken(self, org_id: uuid.UUID, group: str, name: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(tags.c.id).where(tags.c.organization_id == org_id, tags.c.group == group, func.lower(tags.c.name) == name.lower())
        if exclude_id is not None:
            stmt = stmt.where(tags.c.id != exclude_id)
        return self.session.scalar(stmt.limit(1)) is not None

    def add(self, tag: Tag) -> None:
        self.session.add(tag)
        self.session.flush()

    def remove(self, tag: Tag) -> None:
        self.session.delete(tag)
        self.session.flush()


class SqlSubjectLookup:
    def __init__(self, session: Session):
        self.session = session

    def exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        from app.models import Subject  # the subjects table moves with the topics slice

        s = self.session.get(Subject, subject_id)
        return s is not None and s.organization_id == org_id
