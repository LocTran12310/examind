from dataclasses import dataclass
import random
import uuid

from app.modules.assessment.application.common import guard_edit, load_exam
from app.modules.assessment.domain.entities import ExamQuestion
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.modules.assessment.domain.services import exam_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, NotFound


@dataclass(frozen=True)
class SwapExamQuestion:
    exam_id: uuid.UUID
    question_id: uuid.UUID
    seed: int | None = None


class SwapExamQuestionHandler:
    """Another question from the same blueprint row (or of the same type) takes its place, position and points."""

    def __init__(self, exams: ExamRepository, bank: QuestionBank, uow: UnitOfWork):
        self.exams, self.bank, self.uow = exams, bank, uow

    def __call__(self, actor: Actor, cmd: SwapExamQuestion) -> uuid.UUID:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        guard_edit(self.exams, exam)
        eq = self.exams.question(exam.id, cmd.question_id)
        if eq is None:
            raise NotFound("Câu không có trong đề")
        old = self.bank.questions(None, [cmd.question_id])[0]
        f = exam_rules.swap_filter(exam.subject_id, exam.blueprint or [], eq.row, old.type)
        taken = {x.question_id for x in self.exams.questions(exam.id)}
        pool = [i for i in self.bank.pool(actor.org_id, f) if i not in taken]
        if not pool:
            raise Conflict("Không còn câu nào khác phù hợp để đổi", code="no_replacement")
        new_id = random.Random(cmd.seed).choice(pool)
        position, section, points, row = eq.position, eq.section, eq.points, eq.row
        self.exams.remove_question(eq)
        self.exams.add_question(ExamQuestion(exam_id=exam.id, question_id=new_id, position=position, section=section, points=points, row=row))
        self.uow.commit()
        return new_id
