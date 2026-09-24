from dataclasses import dataclass
import uuid

from app.modules.analytics.application.ports import Roster
from app.modules.analytics.domain.ports import WeekRepository
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class StudentWeeklyMastery:
    student_id: uuid.UUID


def series(weeks: WeekRepository, org_id: uuid.UUID, student_id: uuid.UUID) -> dict:
    """{weeks: [{week_start, topics: [{topic_id, mastery, answers}]}]}, oldest week first."""
    out: list[dict] = []
    for row in weeks.series(org_id, student_id):
        if not out or out[-1]["week_start"] != row.week_start:
            out.append({"week_start": row.week_start, "topics": []})
        out[-1]["topics"].append({"topic_id": row.topic_id, "mastery": row.mastery, "answers": row.answers})
    return {"weeks": out}


class MyWeeklyMasteryHandler:
    """A student's own weekly mastery (staff read a student's through StudentWeeklyMastery)."""

    def __init__(self, weeks: WeekRepository):
        self.weeks = weeks

    def __call__(self, actor: Actor) -> dict:
        return series(self.weeks, actor.org_id, actor.user_id)


class StudentWeeklyMasteryHandler:
    """Staff read the weekly mastery of a member of their org."""

    def __init__(self, weeks: WeekRepository, roster: Roster):
        self.weeks, self.roster = weeks, roster

    def __call__(self, actor: Actor, query: StudentWeeklyMastery) -> dict:
        if not self.roster.is_member(actor.org_id, query.student_id):
            raise NotFound("Không tìm thấy học sinh")
        return series(self.weeks, actor.org_id, query.student_id)
