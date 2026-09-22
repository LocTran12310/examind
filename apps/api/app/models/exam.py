# moved to the assessment module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.assessment.domain.entities import (  # noqa: F401
    DEFAULT_POINTS, RESULTS_POLICIES, SECTION_OF_TYPE, AnswerFact, Assignment, AssignmentTarget, Attempt, AttemptAnswer, Exam, ExamQuestion,
)
from app.modules.assessment.infrastructure import orm as _assessment_orm  # noqa: F401
