from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.schemas.documents import ParsedQuestionOut


class ExamIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str = ""
    settings: dict | None = None


class ExamPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str | None = None
    settings: dict | None = None


class ExamQuestionOut(ParsedQuestionOut):
    position: int
    section: str
    points: float
    row: int | None


class ExamOut(BaseModel):
    id: uuid.UUID
    title: str
    subject_id: uuid.UUID | None
    grade: int | None
    description: str
    settings: dict
    blueprint: list
    source: str
    question_count: int
    total_points: float
    created_at: datetime
    questions: list[ExamQuestionOut] = []


class BlueprintIn(BaseModel):
    rows: list[dict]
    seed: int | None = None
    replace: bool = True


class IdsIn(BaseModel):
    question_ids: list[uuid.UUID]


class PointsIn(BaseModel):
    points: float
