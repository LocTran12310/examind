from app.modules.analytics.application.common import Clock, mastery_rows
from app.modules.analytics.domain.ports import MasteryRepository, Topics
from app.shared.application.actor import Actor


class MyMasteryHandler:
    """The caller's own mastery rows. Roles nest (exam-runner-and-roles ADR-02), so staff may ask as well and
    read their own — which is empty, because nobody assigns them work. Reading a *student's* rows is a different
    question with a different answer, and it has its own endpoint (StudentMastery)."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, clock: Clock):
        self.mastery, self.topics, self.clock = mastery, topics, clock

    def __call__(self, actor: Actor) -> list[dict]:
        return mastery_rows(self.mastery, self.topics, actor.org_id, actor.user_id, self.clock())
