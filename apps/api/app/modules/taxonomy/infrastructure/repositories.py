import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.domain.topics import Topic
from app.modules.taxonomy.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.schema.taxonomy import grades, subjects, tags, topics


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

    def groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not tag_ids:
            return {}
        return dict(self.session.execute(select(tags.c.id, tags.c.group).where(tags.c.id.in_(tag_ids), tags.c.organization_id == org_id)).all())

    def find(self, org_id: uuid.UUID, group: str, name: str) -> Tag | None:
        return self.session.scalar(select(Tag).where(tags.c.organization_id == org_id, tags.c.group == group,
                                                     func.lower(tags.c.name) == name.lower()))

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
        return self.session.scalar(select(subjects.c.id).where(subjects.c.id == subject_id, subjects.c.organization_id == org_id)) is not None

    def grade_levels(self, org_id: uuid.UUID) -> set[int]:
        return set(self.session.scalars(select(grades.c.level).where(grades.c.organization_id == org_id)))


class SqlTopicRepository:
    """Topics on ltree paths: subtree depth and subtree moves are single SQL statements."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, org_id: uuid.UUID, topic_id: uuid.UUID) -> Topic | None:
        t = self.session.get(Topic, topic_id)
        return t if t is not None and t.organization_id == org_id else None

    def paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not topic_ids:
            return {}
        return dict(self.session.execute(select(topics.c.id, topics.c.path).where(topics.c.id.in_(topic_ids), topics.c.organization_id == org_id)).all())

    def labels(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str, str]]:
        if not topic_ids:
            return {}
        rows = self.session.execute(select(topics.c.id, topics.c.name, topics.c.path)
                                    .where(topics.c.id.in_(topic_ids), topics.c.organization_id == org_id)).all()
        return {r.id: (r.name, r.path) for r in rows}

    def subject_ids(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID]:
        if not topic_ids:
            return {}
        return dict(self.session.execute(select(topics.c.id, topics.c.subject_id)
                                         .where(topics.c.id.in_(topic_ids), topics.c.organization_id == org_id)).all())

    def children(self, topic_id: uuid.UUID) -> list[Topic]:
        return list(self.session.scalars(select(Topic).where(topics.c.parent_id == topic_id).order_by(topics.c.sort)))

    def has_children(self, topic_id: uuid.UUID) -> bool:
        return self.session.scalar(select(topics.c.id).where(topics.c.parent_id == topic_id).limit(1)) is not None

    def next_sort(self, org_id: uuid.UUID, parent_id: uuid.UUID | None) -> int:
        parent = topics.c.parent_id.is_(None) if parent_id is None else topics.c.parent_id == parent_id
        return self.session.scalar(select(func.coalesce(func.max(topics.c.sort), -1) + 1).where(topics.c.organization_id == org_id, parent)) or 0

    def subtree_depth(self, topic: Topic) -> int:
        return self.session.execute(
            text("select max(nlevel(path)) - nlevel(cast(:p as ltree)) from topics where organization_id=:o and path <@ cast(:p as ltree)"),
            {"p": topic.path, "o": topic.organization_id}).scalar() or 0

    def move(self, topic: Topic, parent_id: uuid.UUID | None, new_path: str) -> None:
        self.session.execute(
            text("""update topics
                       set path = case when path = cast(:old as ltree) then cast(:new as ltree)
                                        else cast(:new as ltree) || subpath(path, nlevel(cast(:old as ltree))) end
                     where organization_id = :o and path <@ cast(:old as ltree)"""),
            {"new": new_path, "old": topic.path, "o": topic.organization_id},
        )
        topic.parent_id = parent_id
        self.session.flush()
        self.session.expire_all()  # the bulk path rewrite bypassed the identity map

    def add(self, topic: Topic) -> None:
        self.session.add(topic)
        self.session.flush()

    def remove(self, topic: Topic) -> None:
        self.session.delete(topic)
        self.session.flush()


# Hooks other contexts register to guard / repoint their references to topics (e.g. question_topics).
REFERENCE_COUNTERS: list = []   # fn(session, org_id, topic_ids) -> int
REFERENCE_MOVERS: list = []     # fn(session, org_id, from_id, to_id) -> None


class SqlTopicReferences:
    def __init__(self, session: Session):
        self.session = session

    def count(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> int:
        return sum(fn(self.session, org_id, topic_ids) for fn in REFERENCE_COUNTERS)

    def repoint(self, org_id: uuid.UUID, from_id: uuid.UUID, to_id: uuid.UUID) -> None:
        for fn in REFERENCE_MOVERS:
            fn(self.session, org_id, from_id, to_id)
