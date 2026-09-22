from dataclasses import dataclass
import uuid

from app.modules.analytics.application.common import mastery_rows
from app.modules.analytics.application.ports import Roster
from app.modules.analytics.domain.ports import MasteryRepository, Topics
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class StudentMastery:
    student_id: uuid.UUID


class StudentMasteryHandler:
    """Staff read the mastery of a member of their org."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, roster: Roster):
        self.mastery, self.topics, self.roster = mastery, topics, roster

    def __call__(self, actor: Actor, query: StudentMastery) -> list[dict]:
        if not self.roster.is_member(actor.org_id, query.student_id):
            raise NotFound("Không tìm thấy học sinh")
        return mastery_rows(self.mastery, self.topics, actor.org_id, query.student_id)
