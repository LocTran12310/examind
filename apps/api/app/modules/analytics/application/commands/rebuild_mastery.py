from dataclasses import dataclass
import uuid

from app.modules.analytics.application.commands.record_answer import record
from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, Topics
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RebuildMastery:
    organization_id: uuid.UUID | None = None  # None: every org


class RebuildMasteryHandler:
    """Mastery rebuilt from the answer facts in grading order (answers graded before mastery tracking existed,
    adaptive-review AC-03); flushed, the caller commits. Returns the number of facts replayed."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, history: AnswerHistory, uow: UnitOfWork):
        self.mastery, self.topics, self.history, self.uow = mastery, topics, history, uow

    def __call__(self, cmd: RebuildMastery) -> int:
        self.mastery.clear(cmd.organization_id)
        n = 0
        for answer in self.history.replay(cmd.organization_id):
            if record(self.mastery, self.topics, answer):
                self.uow.flush()
            n += 1
        return n
