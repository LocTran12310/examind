from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class TagView:
    id: uuid.UUID
    group: str
    name: str
    subject_id: uuid.UUID | None


def tag_view(t) -> TagView:
    return TagView(id=t.id, group=t.group, name=t.name, subject_id=t.subject_id)


@dataclass(frozen=True)
class TopicView:
    id: uuid.UUID
    subject_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    level_kind: str
    grade: int | None
    path: str
    depth: int
    sort: int
    child_count: int = 0


def topic_view(t, child_count: int = 0) -> TopicView:
    return TopicView(id=t.id, subject_id=t.subject_id, parent_id=t.parent_id, name=t.name, level_kind=t.level_kind, grade=t.grade,
                     path=t.path, depth=t.path.count(".") + 1, sort=t.sort, child_count=child_count)


@dataclass(frozen=True)
class SubjectView:
    id: uuid.UUID
    code: str
    name: str


@dataclass(frozen=True)
class GradeRef:
    id: uuid.UUID
    level: int
    name: str
    school_level_id: uuid.UUID | None = None
    school_level_name: str | None = None


@dataclass(frozen=True)
class SemesterView:
    id: uuid.UUID
    code: str
    name: str


@dataclass(frozen=True)
class TaxonomyView:
    subjects: list[SubjectView]
    grades: list[GradeRef]
    semesters: list[SemesterView]
