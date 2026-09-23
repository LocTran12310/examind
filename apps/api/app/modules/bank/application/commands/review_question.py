from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import load_question, record, spot_feedback
from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, ReviewSettings
from app.modules.bank.domain.services import review
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Invalid
from app.shared.domain.ids import new_id

ACTIONS = ("approve", "reject", "restore", "skip")


@dataclass(frozen=True)
class ReviewQuestion:
    question_id: uuid.UUID
    action: str  # approve | reject | restore | skip


class ReviewQuestionHandler:
    """One decision in the review queue. Approving / rejecting a spot check is recorded as spot_ok / spot_fail."""

    def __init__(self, questions: QuestionRepository, log: ReviewLog, settings: ReviewSettings, views: QuestionViews, uow: UnitOfWork):
        self.questions, self.log, self.settings, self.views, self.uow = questions, log, settings, views, uow

    def __call__(self, actor: Actor, cmd: ReviewQuestion) -> QuestionView:
        batch = new_id()
        q = load_question(self.questions, actor.org_id, cmd.question_id)
        before = q.snapshot()
        was_spot = q.is_spot_pending
        if cmd.action == "approve":
            review.approve(q, actor.user_id, utcnow())
            record(self.log, actor, q, "spot_ok" if was_spot else "approve", before, q.snapshot(), batch)
        elif cmd.action == "reject":
            review.reject(q, actor.user_id, utcnow())
            record(self.log, actor, q, "spot_fail" if was_spot else "reject", before, q.snapshot(), batch)
            if was_spot:
                spot_feedback(self.log, self.settings, actor, batch)
        elif cmd.action == "restore":
            review.restore(q, self.settings.threshold(actor.org_id))
            record(self.log, actor, q, "restore", before, q.snapshot(), batch)
        elif cmd.action == "skip":
            record(self.log, actor, q, "skip", None, None, batch)
        else:
            raise Invalid("Thao tác không hợp lệ")
        self.uow.commit()
        return self.views.views([q])[0]
