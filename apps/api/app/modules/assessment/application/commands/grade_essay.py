from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import Grading, load_attempt
from app.modules.assessment.domain.entities import STAFF_ROLES
from app.modules.assessment.domain.ports import AttemptRepository, QuestionBank
from app.modules.assessment.domain.services import attempt_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden, NotFound


@dataclass(frozen=True)
class GradeEssay:
    attempt_id: uuid.UUID
    question_id: uuid.UUID
    points: float
    comment: str | None = None


class GradeEssayHandler:
    """A teacher's points (0..max) and comment on a submitted answer; the attempt's total and the answer fact follow."""

    def __init__(self, attempts: AttemptRepository, bank: QuestionBank, grading: Grading, uow: UnitOfWork):
        self.attempts, self.bank, self.grading, self.uow = attempts, bank, grading, uow

    def __call__(self, actor: Actor, cmd: GradeEssay) -> dict:
        att = load_attempt(self.attempts, actor, cmd.attempt_id)
        if actor.role not in STAFF_ROLES:
            raise Forbidden()
        if att.status == "submitted":
            ans = self.attempts.answer(att.id, cmd.question_id)
            if ans is None:
                raise NotFound("Không có câu trả lời")
        else:
            ans = None
        attempt_rules.grade_essay(att, ans, cmd.points, cmd.comment, actor.user_id)
        self.attempts.flush()
        self.grading.record(att, self.bank.questions(None, [cmd.question_id])[0], ans)
        attempt_rules.regraded(att, self.attempts.answers(att.id))
        self.uow.commit()
        return {"score": att.score, "needs_grading": att.needs_grading}
