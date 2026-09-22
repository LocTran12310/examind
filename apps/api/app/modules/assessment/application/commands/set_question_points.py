from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.ports import ExamRepository
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class SetQuestionPoints:
    exam_id: uuid.UUID
    question_id: uuid.UUID
    points: float


class SetQuestionPointsHandler:
    def __init__(self, exams: ExamRepository, uow: UnitOfWork):
        self.exams, self.uow = exams, uow

    def __call__(self, actor: Actor, cmd: SetQuestionPoints) -> None:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        points = exam_rules.check_points(cmd.points)
        eq = self.exams.question(exam.id, cmd.question_id)
        if eq is None:
            raise NotFound("Câu không có trong đề")
        eq.points = points
        self.uow.commit()
