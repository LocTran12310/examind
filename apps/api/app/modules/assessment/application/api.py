"""What other contexts (and the old layout) may ask assessment (architecture-refactor ADR-01)."""
from datetime import datetime
import uuid

from app.modules.assessment.application.commands.create_exam_from_document import (
    CreateExamFromDocument, CreateExamFromDocumentHandler,
)
from app.modules.assessment.application.commands.start_attempt import new_attempt
from app.modules.assessment.application.commands.sweep_expired_attempts import SweepExpiredAttemptsHandler
from app.modules.assessment.application.common import Clock, Grading
from app.modules.assessment.domain.entities import Attempt
from app.modules.assessment.domain.ports import AttemptRepository, ExamRepository, QuestionBank, Subjects
from app.modules.assessment.domain.value_objects import DocumentRef
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


class AssessmentApi:
    def __init__(self, exams: ExamRepository, attempts: AttemptRepository, bank: QuestionBank, subjects: Subjects, grading: Grading,
                 clock: Clock, uow: UnitOfWork):
        self.exams, self.attempts, self.bank, self.subjects, self.grading, self.clock, self.uow = (
            exams, attempts, bank, subjects, grading, clock, uow)

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
