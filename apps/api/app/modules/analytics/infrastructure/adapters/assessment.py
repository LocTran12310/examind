"""Assessment port over the assessment context's application API, handed in by the composition root: analytics never
imports another module."""
from datetime import datetime
from typing import Any, Protocol
import uuid

from app.modules.analytics.domain.value_objects import PracticeAttempt, ReviewStatus


class _AssessmentApi(Protocol):
    def create_personal_exam(self, org_id: uuid.UUID, title: str, created_by: uuid.UUID | None, adaptive: dict,
                             question_ids: list[uuid.UUID]) -> uuid.UUID: ...

    def new_attempt(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, deadline: datetime) -> Any: ...

    def assign_personal(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, title: str, open_at: datetime,
                        close_at: datetime, duration_minutes: int, created_by: uuid.UUID | None) -> uuid.UUID: ...

    def practice_attempts(self, student_id: uuid.UUID, limit: int = 20) -> list: ...

    def latest_personal_review(self, student_id: uuid.UUID) -> Any: ...


class AssessmentExams:
    def __init__(self, assessment: _AssessmentApi):
        self.assessment = assessment

    def create_exam(self, org_id: uuid.UUID, title: str, created_by: uuid.UUID | None, adaptive: dict,
                    question_ids: list[uuid.UUID]) -> uuid.UUID:
        return self.assessment.create_personal_exam(org_id, title, created_by, adaptive, list(question_ids))

    def start_attempt(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, deadline: datetime) -> uuid.UUID:
        return self.assessment.new_attempt(org_id, exam_id, student_id, deadline).id

    def assign(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, title: str, open_at: datetime, close_at: datetime,
               duration_minutes: int, created_by: uuid.UUID | None) -> uuid.UUID:
        return self.assessment.assign_personal(org_id, exam_id, student_id, title, open_at, close_at, duration_minutes, created_by)

    def practice_attempts(self, student_id: uuid.UUID, limit: int) -> list[PracticeAttempt]:
        return [PracticeAttempt(r.attempt_id, r.title, r.status, r.started_at, r.submitted_at, r.score10, r.settings)
                for r in self.assessment.practice_attempts(student_id, limit)]

    def latest_review(self, student_id: uuid.UUID) -> ReviewStatus | None:
        r = self.assessment.latest_personal_review(student_id)
        return ReviewStatus(r.assignment_id, r.title, r.status) if r else None
