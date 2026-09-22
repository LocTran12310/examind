from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import load_exam
from app.modules.assessment.application.dto import ExamQuestionView
from app.modules.assessment.application.ports import ExamReader
from app.modules.assessment.domain.ports import ExamRepository, QuestionBank
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchExamQuestions:
    exam_id: uuid.UUID
    request: SearchRequest


class SearchExamQuestionsHandler:
    """One exam's questions as a server-side table (the exam list never embeds them)."""

    def __init__(self, exams: ExamRepository, reader: ExamReader, bank: QuestionBank):
        self.exams, self.reader, self.bank = exams, reader, bank

    def __call__(self, actor: Actor, query: SearchExamQuestions) -> Page[ExamQuestionView]:
        exam = load_exam(self.exams, actor.org_id, query.exam_id)
        page = self.reader.questions(exam.id, query.request)
        views = self.bank.views(None, [r.question_id for r in page.data])
        rows = [ExamQuestionView(views[r.question_id], r.position, r.section, r.points, r.row) for r in page.data if r.question_id in views]
        return Page(rows, page.total, page.page, page.limit)
