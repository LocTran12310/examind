from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import load_attempt
from app.modules.assessment.domain.ports import AttemptRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RecordTabSwitch:
    attempt_id: uuid.UUID


class RecordTabSwitchHandler:
    """The runner reports leaving the tab; only the student's own running attempt counts."""

    def __init__(self, attempts: AttemptRepository, uow: UnitOfWork):
        self.attempts, self.uow = attempts, uow

    def __call__(self, actor: Actor, cmd: RecordTabSwitch) -> int:
        att = load_attempt(self.attempts, actor, cmd.attempt_id)
        if att.student_id != actor.user_id or att.status != "in_progress":
            return att.tab_switches
        n = self.attempts.count_tab_switch(att)
        self.uow.commit()
        return n
