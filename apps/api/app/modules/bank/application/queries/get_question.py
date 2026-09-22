from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import load_question
from app.modules.bank.application.dto import QuestionView, student_view
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.ports import QuestionRepository
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetQuestion:
    question_id: uuid.UUID


class GetQuestionHandler:
    """Staff see everything; students never receive answers or solutions here (exams show them after submission)."""

    def __init__(self, questions: QuestionRepository, views: QuestionViews):
        self.questions, self.views = questions, views

    def __call__(self, actor: Actor, query: GetQuestion) -> QuestionView:
        q = load_question(self.questions, actor.org_id, query.question_id)
        if actor.role == "student":
            return student_view(q)
        return self.views.views([q])[0]
