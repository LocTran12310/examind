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
