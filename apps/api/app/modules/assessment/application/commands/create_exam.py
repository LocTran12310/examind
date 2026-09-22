from dataclasses import dataclass
import uuid

from app.modules.assessment.domain.entities import Exam
from app.modules.assessment.domain.ports import ExamRepository, Subjects
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class CreateExam:
    title: str
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str = ""
    settings: dict | None = None
    source: str = "manual"


def new_exam(exams: ExamRepository, subjects: Subjects, actor: Actor, cmd: CreateExam) -> Exam:
    """Flushed, not committed (drafting from a document shares the caller's transaction)."""
    title = exam_rules.title_of(cmd.title)
    if cmd.subject_id and not subjects.exists(actor.org_id, cmd.subject_id):
        raise Invalid("Môn học không hợp lệ", "subject_id")
    exam = Exam(organization_id=actor.org_id, title=title, subject_id=cmd.subject_id, grade=cmd.grade, description=cmd.description or "",
                settings=exam_rules.normalized_settings(cmd.settings), created_by=actor.user_id, source=cmd.source)
    exams.add(exam)
    return exam


class CreateExamHandler:
    def __init__(self, exams: ExamRepository, subjects: Subjects, uow: UnitOfWork):
        self.exams, self.subjects, self.uow = exams, subjects, uow

    def __call__(self, actor: Actor, cmd: CreateExam) -> uuid.UUID:
        exam = new_exam(self.exams, self.subjects, actor, cmd)
        self.uow.commit()
        return exam.id
