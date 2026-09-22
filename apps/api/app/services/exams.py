"""The exam builder moved to app.modules.assessment (architecture-refactor UOW-06); what the old layout still calls."""
from app.modules.assessment.domain.entities import Exam


def points_for(exam: Exam, qtype: str) -> float:
    return exam.points_for(qtype)
