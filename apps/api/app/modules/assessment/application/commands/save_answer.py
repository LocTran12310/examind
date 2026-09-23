from dataclasses import dataclass
from datetime import datetime
import uuid

from app.modules.assessment.application.common import Clock, Grading, load_attempt
from app.modules.assessment.domain.entities import AttemptAnswer
from app.modules.assessment.domain.ports import AttemptRepository, QuestionBank
from app.modules.assessment.domain.services import attempt_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden, NotFound


@dataclass(frozen=True)
class SaveAnswer:
    attempt_id: uuid.UUID
    question_id: uuid.UUID
    response: dict | None
    seconds_spent: int | None = None  # what the runner measured since the last save
    first_seen_at: datetime | None = None


class SaveAnswerHandler:
    """Autosave of one answer while the attempt runs (past the deadline the attempt is closed instead); MCQ choices
    arrive in the shown labels and are stored in the original ones. Each save carries the seconds the question was on
    screen, which the attempt accumulates and clamps (learning-telemetry ADR-01)."""

    def __init__(self, attempts: AttemptRepository, bank: QuestionBank, grading: Grading, clock: Clock, uow: UnitOfWork):
        self.attempts, self.bank, self.grading, self.clock, self.uow = attempts, bank, grading, clock, uow

    def __call__(self, actor: Actor, cmd: SaveAnswer) -> dict:
        att = load_attempt(self.attempts, actor, cmd.attempt_id)
        if att.student_id != actor.user_id:
            raise Forbidden()
        attempt_rules.check_open(att)
        if self.grading.finalize_if_expired(att):
            attempt_rules.check_open(att)
        if str(cmd.question_id) not in att.question_order:
            raise NotFound("Câu hỏi không thuộc bài làm")
        q = self.bank.questions(None, [cmd.question_id])[0]
        clean = attempt_rules.checked_response(q, attempt_rules.from_display(att, q, cmd.response))
        ans = self.attempts.answer(att.id, q.id)
        if ans is None:
            ans = AttemptAnswer(attempt_id=att.id, question_id=q.id)
            self.attempts.add_answer(ans)
        ans.response = clean
        now = self.clock()
        ans.updated_at = now
        attempt_rules.track_timing(att, ans, cmd.seconds_spent, cmd.first_seen_at, now)
        self.uow.commit()
        return {"question_id": ans.question_id, "response": attempt_rules.to_display(att, q, ans.response),
                "saved_at": ans.updated_at, "seconds_spent": ans.seconds_spent}
