from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.ports import ExamRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteExam:
    exam_id: uuid.UUID


class DeleteExamHandler:
    def __init__(self, exams: ExamRepository, uow: UnitOfWork):
        self.exams, self.uow = exams, uow

    def __call__(self, actor: Actor, cmd: DeleteExam) -> None:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        self.exams.remove(exam)
        self.uow.commit()
