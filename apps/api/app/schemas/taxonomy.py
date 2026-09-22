import uuid

from pydantic import BaseModel, Field


class SubjectOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class GradeOut(BaseModel):
    id: uuid.UUID
    level: int
    name: str
    school_level_id: uuid.UUID | None = None
    school_level_name: str | None = None


class SemesterOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class TaxonomyOut(BaseModel):
    subjects: list[SubjectOut]
    grades: list[GradeOut]
    semesters: list[SemesterOut]


class TopicOut(BaseModel):
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


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    level_kind: str | None = None
    grade: int | None = None


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    level_kind: str | None = None
    grade: int | None = None
    sort: int | None = None


class TopicMove(BaseModel):
    parent_id: uuid.UUID | None


class TopicMerge(BaseModel):
    target_id: uuid.UUID


class TagOut(BaseModel):
    id: uuid.UUID
    group: str
    name: str
    subject_id: uuid.UUID | None = None


class TagIn(BaseModel):
    group: str = "custom"
    name: str = Field(min_length=1, max_length=100)
    subject_id: uuid.UUID | None = None


class TagUpdate(BaseModel):
    group: str | None = None
    name: str | None = Field(default=None, max_length=100)
    subject_id: uuid.UUID | None = None  # sent as null = make it shared


def topic_out(t, child_count=0) -> TopicOut:
    return TopicOut(id=t.id, subject_id=t.subject_id, parent_id=t.parent_id, name=t.name, level_kind=t.level_kind,
                    grade=t.grade, path=t.path, depth=t.path.count(".") + 1, sort=t.sort, child_count=child_count)
