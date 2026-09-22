from typing import Protocol
import uuid

from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.domain.topics import Topic


class TagRepository(Protocol):
    def get(self, org_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None: ...

    def name_taken(self, org_id: uuid.UUID, group: str, name: str, exclude_id: uuid.UUID | None = None) -> bool: ...

    def groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """The group of each tag of the org among `tag_ids`."""
        ...

    def add(self, tag: Tag) -> None: ...

    def remove(self, tag: Tag) -> None: ...


class SubjectLookup(Protocol):
    def exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...


class TopicRepository(Protocol):
    def get(self, org_id: uuid.UUID, topic_id: uuid.UUID) -> Topic | None: ...

    def paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """The ltree path of each topic of the org among `topic_ids`."""
        ...

    def children(self, topic_id: uuid.UUID) -> list[Topic]:
        """Direct children, by sort."""
        ...

    def has_children(self, topic_id: uuid.UUID) -> bool: ...

    def next_sort(self, org_id: uuid.UUID, parent_id: uuid.UUID | None) -> int: ...

    def subtree_depth(self, topic: Topic) -> int:
        """Levels below `topic` (0 for a leaf)."""
        ...

    def move(self, topic: Topic, parent_id: uuid.UUID | None, new_path: str) -> None:
        """Re-parent `topic` and rewrite the paths of its whole subtree."""
        ...

    def add(self, topic: Topic) -> None: ...

    def remove(self, topic: Topic) -> None: ...


class TopicReferences(Protocol):
    """What points at topics from other contexts (question tags…): counted before a delete, repointed on a merge."""

    def count(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> int: ...

    def repoint(self, org_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID) -> None: ...

