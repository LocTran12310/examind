from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import load_exam
from app.modules.assessment.application.dto import ExamQuestionView, ExamView
from app.modules.assessment.domain.entities import Exam
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetExam:
    exam_id: uuid.UUID


def exam_view(exams: ExamRepository, bank: QuestionBank, exam: Exam) -> ExamView:
    """The exam with every question (the bank's view plus position, section, points, blueprint row), by position."""
    eqs = exams.questions(exam.id)
    views = bank.views(None, [eq.question_id for eq in eqs])
    qs = [ExamQuestionView(views[eq.question_id], eq.position, eq.section, eq.points, eq.row) for eq in eqs if eq.question_id in views]
    return ExamView(exam, len(eqs), round(sum(eq.points for eq in eqs), 4), qs)


class GetExamHandler:
    def __init__(self, exams: ExamRepository, bank: QuestionBank):
        self.exams, self.bank = exams, bank

    def __call__(self, actor: Actor, query: GetExam) -> ExamView:
        return exam_view(self.exams, self.bank, load_exam(self.exams, actor.org_id, query.exam_id))
