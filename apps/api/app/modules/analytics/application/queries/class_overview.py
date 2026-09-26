from dataclasses import dataclass
import uuid

from app.modules.analytics.application.common import Clock, mastery_rows
from app.modules.analytics.application.ports import Roster
from app.modules.analytics.domain.ports import Assessment, MasteryRepository, Topics
from app.modules.analytics.domain.services.mastery import weak_topics
from app.modules.analytics.domain.services.practice import PLAN_TOPICS
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class ClassOverview:
    class_id: uuid.UUID


class ClassOverviewHandler:
    """Per student of a class: the weakest topics with enough answers behind them (ADR-04) and the latest personal
    review with its status."""

    def __init__(self, mastery: MasteryRepository, topics: Topics, roster: Roster, assessment: Assessment, clock: Clock):
        self.mastery, self.topics, self.roster, self.assessment, self.clock = mastery, topics, roster, assessment, clock

    def __call__(self, actor: Actor, query: ClassOverview) -> list[dict]:
        out = []
        for u in self.roster.class_members(actor, query.class_id):
            if u.role != "student":
                continue
            review = self.assessment.latest_review(actor.org_id, u.id)
            rows = mastery_rows(self.mastery, self.topics, actor.org_id, u.id, self.clock())
            out.append({"student_id": u.id, "full_name": u.full_name, "username": u.username,
                        "weakest": [{"name": r["name"], "mastery": r["mastery"], "answers": r["answers"]} for r in weak_topics(rows, PLAN_TOPICS)],
                        "review": {"assignment_id": review.assignment_id, "title": review.title, "status": review.status,
                                   "open_at": review.open_at, "close_at": review.close_at, "total": review.total} if review else None})
        return out
