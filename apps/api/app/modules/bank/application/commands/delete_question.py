from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import load_question, record
from app.modules.bank.domain.ports import QuestionRepository, QuestionUsage, ReviewLog
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict
from app.shared.domain.ids import new_id


@dataclass(frozen=True)
class DeleteQuestion:
    question_id: uuid.UUID


class DeleteQuestionHandler:
    """Only a question nothing uses (an exam keeps its questions: reject it instead); its duplicates go back to review."""

    def __init__(self, questions: QuestionRepository, usage: QuestionUsage, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.usage, self.log, self.uow = questions, usage, log, uow

    def __call__(self, actor: Actor, cmd: DeleteQuestion) -> None:
        q = load_question(self.questions, actor.org_id, cmd.question_id)
        if self.usage.in_use(q.id):
            raise Conflict("Câu hỏi đang được dùng trong đề — hãy loại thay vì xóa", code="question_in_use")
        record(self.log, actor, q, "reject", q.snapshot(), {"deleted": True}, new_id())
        self.questions.release_duplicates_of([q.id])
        self.questions.remove(q)
        self.uow.commit()
