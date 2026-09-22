"""Maps the assessment dataclasses onto their tables (architecture-refactor ADR-01). Importing this module is enough;
mapping happens once."""
from app.modules.assessment.domain.entities import (
    AnswerFact,
    Assignment,
    AssignmentTarget,
    Attempt,
    AttemptAnswer,
    Exam,
    ExamQuestion,
)
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.assessment import (
    answer_facts,
    assignment_targets,
    assignments,
    attempt_answers,
    attempts,
    exam_questions,
    exams,
)


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


for _cls, _table in ((Exam, exams), (ExamQuestion, exam_questions), (Assignment, assignments), (AssignmentTarget, assignment_targets),
                     (Attempt, attempts), (AttemptAnswer, attempt_answers), (AnswerFact, answer_facts)):
    if not _mapped(_cls):
        mapper_registry.map_imperatively(_cls, _table)
