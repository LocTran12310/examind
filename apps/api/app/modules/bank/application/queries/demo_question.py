from app.modules.bank.application.dto import QuestionView, question_view
from app.modules.bank.application.ports import QuestionReader
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


class DemoQuestionHandler:
    """The seeded sample question (renderer preview)."""

    def __init__(self, reader: QuestionReader):
        self.reader = reader

    def __call__(self, actor: Actor) -> QuestionView:
        q = self.reader.demo(actor.org_id)
        if q is None:
            raise NotFound("Chưa có câu hỏi mẫu")
        return question_view(q)
