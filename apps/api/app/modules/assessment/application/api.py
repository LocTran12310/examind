"""What other contexts may ask assessment (architecture-refactor ADR-01)."""
from datetime import datetime
import uuid

from app.modules.assessment.application.commands.assign_personal_exam import AssignPersonalExam, AssignPersonalExamHandler
from app.modules.assessment.application.commands.create_exam_from_document import (
    CreateExamFromDocument,
    CreateExamFromDocumentHandler,
)
from app.modules.assessment.application.commands.create_personal_exam import CreatePersonalExam, CreatePersonalExamHandler
from app.modules.assessment.application.commands.start_attempt import new_attempt
from app.modules.assessment.application.commands.sweep_expired_attempts import SweepExpiredAttemptsHandler
from app.modules.assessment.application.common import Clock, Grading
from app.modules.assessment.application.dto import PersonalReviewRow, PracticeAttemptRow
from app.modules.assessment.application.ports import PersonalReader
from app.modules.assessment.domain.entities import Attempt
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository, QuestionBank, Subjects
from app.modules.assessment.domain.value_objects import DocumentRef
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


class AssessmentApi:
    def __init__(self, exams: ExamRepository, attempts: AttemptRepository, assignments: AssignmentRepository, bank: QuestionBank,
                 subjects: Subjects, grading: Grading, personal: PersonalReader, clock: Clock, uow: UnitOfWork):
        self.exams, self.attempts, self.assignments, self.bank, self.subjects, self.grading, self.personal, self.clock, self.uow = (
            exams, attempts, assignments, bank, subjects, grading, personal, clock, uow)

    def exam_from_document(self, actor: Actor, document_id: uuid.UUID, filename: str, status: str, meta: dict,
                           title: str | None = None) -> dict:
        """A draft exam from a parsed document (ingestion): {exam_id, added, skipped}; flushed with the caller's transaction."""
        return CreateExamFromDocumentHandler(self.exams, self.bank, self.subjects, self.uow)(
            actor, CreateExamFromDocument(DocumentRef(document_id, filename, status, dict(meta or {})), title))

    def question_in_use(self, question_id: uuid.UUID) -> bool:
        """An exam uses the question (the bank keeps it then)."""
        return self.exams.uses_question(question_id)

    def new_attempt(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, deadline: datetime,
                    assignment_id: uuid.UUID | None = None, shuffle_questions: bool = True, shuffle_options: bool = True) -> Attempt:
        """An attempt at an exam outside an assignment (personal practice); flushed with the caller's transaction."""
        att = new_attempt(self.exams, self.bank, self.attempts, org_id, exam_id, student_id, deadline, assignment_id,
                          shuffle_questions, shuffle_options)
        self.uow.flush()
        return att

    def sweep_expired(self) -> int:
        """Close abandoned attempts (the worker); flushed, the caller commits."""
        return SweepExpiredAttemptsHandler(self.attempts, self.grading, self.clock)()

    # ------------------------------------------------------------------ analytics (personal review exams)

    def create_personal_exam(self, org_id: uuid.UUID, title: str, created_by: uuid.UUID | None, adaptive: dict,
                             question_ids: list[uuid.UUID], subject_id: uuid.UUID | None = None) -> uuid.UUID:
        """A personal review exam from analytics' plan; flushed with the caller's transaction."""
        return CreatePersonalExamHandler(self.exams, self.bank, self.uow)(
            CreatePersonalExam(org_id, title, created_by, dict(adaptive), tuple(question_ids), subject_id))

    def assign_personal(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, title: str, open_at: datetime,
                        close_at: datetime, duration_minutes: int, created_by: uuid.UUID | None) -> uuid.UUID:
        """The exam given to its one student; flushed with the caller's transaction."""
        return AssignPersonalExamHandler(self.assignments, self.uow)(
            AssignPersonalExam(org_id, exam_id, student_id, title, open_at, close_at, duration_minutes, created_by))

    def practice_attempts(self, org_id: uuid.UUID, student_id: uuid.UUID, limit: int = 20) -> list[PracticeAttemptRow]:
        return self.personal.practice_attempts(org_id, student_id, limit)

    def latest_personal_review(self, org_id: uuid.UUID, student_id: uuid.UUID) -> PersonalReviewRow | None:
        return self.personal.latest_review(org_id, student_id)
