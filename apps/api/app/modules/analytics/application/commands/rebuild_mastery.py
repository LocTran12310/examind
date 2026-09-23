from dataclasses import dataclass
import uuid

from app.modules.analytics.application.commands.record_answer import record
from app.modules.analytics.application.dto import RebuildResult
from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, Topics
from app.modules.analytics.domain.services.mastery import check_rebuilder
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RebuildMastery:
    """Nothing to say: an admin only ever replays their own organisation (the actor's)."""


def replay(mastery: MasteryRepository, topics: Topics, history: AnswerHistory, uow: UnitOfWork,
           org_id: uuid.UUID | None) -> RebuildResult:
    """Mastery of the org (of every org when None) rebuilt from its answer facts in grading order; flushed, the
    caller commits. Decay is part of the rules, so the replay lands on the numbers live grading left."""
    mastery.clear(org_id)
    students: set[uuid.UUID] = set()
    moved: set[uuid.UUID] = set()
    facts = 0
    for answer in history.replay(org_id):
        topic_id = record(mastery, topics, answer)
        if topic_id is not None:
            uow.flush()
            students.add(answer.student_id)
            moved.add(topic_id)
        facts += 1
    return RebuildResult(students=len(students), topics=len(moved), facts=facts)


class RebuildMasteryHandler:
    """An org admin replays their organisation's answer facts (learning-telemetry A-07), in one transaction. The
    bootstrap's backfill of answers graded before mastery tracking existed goes through AnalyticsApi instead."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, history: AnswerHistory, uow: UnitOfWork):
        self.mastery, self.topics, self.history, self.uow = mastery, topics, history, uow

    def __call__(self, actor: Actor, cmd: RebuildMastery) -> RebuildResult:
        check_rebuilder(actor.role)
        result = replay(self.mastery, self.topics, self.history, self.uow, actor.org_id)
        self.uow.commit()
        return result
