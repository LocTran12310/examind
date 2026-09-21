import uuid

from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: uuid.UUID
    type: str
    stem: str
    options: list[dict]
    answer: dict | None
    solution: str
    difficulty: str | None
    grade: int | None
    status: str


def question_out(q, hide_answer: bool = False) -> QuestionOut:
    options = q.options or []
    if hide_answer:
        options = [{k: v for k, v in o.items() if k != "is_true"} for o in options]
    return QuestionOut(id=q.id, type=q.type, stem=q.stem, options=options,
                       answer=None if hide_answer else q.answer, solution="" if hide_answer else q.solution,
                       difficulty=q.difficulty, grade=q.grade, status=q.status)


class QuestionPatch(BaseModel):
    type: str | None = None
    stem: str | None = None
    options: list[dict] | None = None
    answer: dict | None = None
    solution: str | None = None
    difficulty: str | None = None
    grade: int | None = None
    topic_ids: list[uuid.UUID] | None = None
    primary_topic_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] | None = None


class ActionIn(BaseModel):
    action: str
