from app.modules.analytics.application.common import Clock, mastery_rows
from app.modules.analytics.domain.ports import MasteryRepository, Topics
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden


class MyMasteryHandler:
    """A student's own mastery rows (staff read a student's through StudentMastery)."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, clock: Clock):
        self.mastery, self.topics, self.clock = mastery, topics, clock

    def __call__(self, actor: Actor) -> list[dict]:
        if actor.role != "student":
            raise Forbidden()
        return mastery_rows(self.mastery, self.topics, actor.org_id, actor.user_id, self.clock())
