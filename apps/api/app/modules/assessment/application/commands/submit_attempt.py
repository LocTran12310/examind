from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import Clock, Grading, load_attempt
from app.modules.assessment.domain.ports import AttemptRepository
from app.modules.assessment.domain.services import attempt_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class SubmitAttempt:
    attempt_id: uuid.UUID


class SubmitAttemptHandler:
    """The student hands in; past the deadline it counts as an automatic close (dated at the deadline)."""

    def __init__(self, attempts: AttemptRepository, grading: Grading, clock: Clock, uow: UnitOfWork):
        self.attempts, self.grading, self.clock, self.uow = attempts, grading, clock, uow

    def __call__(self, actor: Actor, cmd: SubmitAttempt) -> dict:
        att = load_attempt(self.attempts, actor, cmd.attempt_id)
        if att.student_id != actor.user_id:
            raise Forbidden()
        self.grading.submit(att, auto=attempt_rules.expired(att, self.clock()))
        self.uow.commit()
        return {"id": att.id, "status": att.status}
