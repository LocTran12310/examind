from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.ports import ExamRepository
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RemoveExamQuestion:
    exam_id: uuid.UUID
    question_id: uuid.UUID


class RemoveExamQuestionHandler:
    def __init__(self, exams: ExamRepository, uow: UnitOfWork):
        self.exams, self.uow = exams, uow

    def __call__(self, actor: Actor, cmd: RemoveExamQuestion) -> None:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        eq = self.exams.question(exam.id, cmd.question_id)
        if eq is not None:
            self.exams.remove_question(eq)
        exam_rules.renumbered(self.exams.questions(exam.id))
        self.uow.commit()
