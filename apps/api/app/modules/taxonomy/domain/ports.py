from typing import Protocol
import uuid

from app.modules.taxonomy.domain.entities import Tag


class TagRepository(Protocol):
    def get(self, org_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None: ...

    def name_taken(self, org_id: uuid.UUID, group: str, name: str, exclude_id: uuid.UUID | None = None) -> bool: ...

    def add(self, tag: Tag) -> None: ...

    def remove(self, tag: Tag) -> None: ...


class SubjectLookup(Protocol):
    def exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...
