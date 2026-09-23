from dataclasses import dataclass
from datetime import date
import uuid

from app.modules.analytics.application.common import Clock
from app.modules.analytics.domain.entities import TopicWeek
from app.modules.analytics.domain.ports import AnswerHistory, Topics, WeekRepository
from app.modules.analytics.domain.services import mastery as mastery_rules
from app.modules.analytics.domain.services.weeks import WEEK, every_week, week_start
from app.modules.analytics.domain.value_objects import AnswerRecord
from app.shared.application.calendar import BusinessCalendar
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class SnapshotWeek:
    week_start: date | None = None  # None: the business week running now
    organization_id: uuid.UUID | None = None  # None: every org


@dataclass(frozen=True)
class BackfillWeeks:
    organization_id: uuid.UUID | None = None


class WeeklySnapshot:
    """Where every student's mastery of every topic stood when a business week closed, and how many answers that week
    saw (learning-telemetry A-06). The weekly job and the backfill replay the answer facts by the same rules, so a
    week written while it runs and the same week derived later hold the same numbers."""

    def __init__(self, weeks: WeekRepository, topics: Topics, history: AnswerHistory, cal: BusinessCalendar, clock: Clock,
                 uow: UnitOfWork):
        self.weeks, self.topics, self.history, self.cal, self.clock, self.uow = weeks, topics, history, cal, clock, uow

    def week(self, monday: date, org_id: uuid.UUID | None) -> int:
        return self._write(list(self.history.replay(org_id)), [monday], org_id)

    def backfill(self, org_id: uuid.UUID | None) -> int:
        """Every week from the first answer fact to the last, including the ones nobody answered in."""
        answers = list(self.history.replay(org_id))
        days = [self.cal.day_of(a.at) for a in answers if a.at is not None]
        if not days:
            return 0
        self.weeks.clear(org_id)
        return self._write(answers, every_week(min(days), max(max(days), self.cal.today())), org_id)

    def _write(self, answers: list[AnswerRecord], targets: list[date], org_id: uuid.UUID | None) -> int:
        """`answers` in grading order, replayed; at the close of each target week the state so far is written out."""
        acc = mastery_rules.Accumulator()
        counts: dict[tuple[uuid.UUID, uuid.UUID], int] = {}
        now = self.clock()
        seen, written = 0, 0
        for monday in targets:
            opens, closes = self.cal.start_of(monday), self.cal.start_of(monday + WEEK)
            stands = min(closes, now)  # a week still running is snapshotted where mastery stands, not where it will
            while seen < len(answers) and (answers[seen].at is None or answers[seen].at < closes):
                a = answers[seen]
                seen += 1
                topic_id = self.topics.id_by_path(a.organization_id, a.topic_path) if a.topic_path else None
                if topic_id is None:
                    continue
                acc.add(a.student_id, topic_id, a.organization_id, a.correct_ratio, a.difficulty, a.at)
                if a.at is not None and a.at >= opens:
                    counts[(a.student_id, topic_id)] = counts.get((a.student_id, topic_id), 0) + 1
            self.weeks.clear(org_id, monday)
            for key, row in acc.rows.items():
                self.weeks.put(TopicWeek(key[0], key[1], row.organization_id, monday,
                                         mastery_rules.decay(row.mastery, row.last_at, stands), counts.get(key, 0)))
                written += 1
            counts = {}
        self.uow.commit()
        return written


class SnapshotWeekHandler:
    """One business week written out — what the worker runs for the week in progress."""

    def __init__(self, snapshot: WeeklySnapshot, cal: BusinessCalendar):
        self.snapshot, self.cal = snapshot, cal

    def __call__(self, cmd: SnapshotWeek) -> int:
        return self.snapshot.week(cmd.week_start or week_start(self.cal.today()), cmd.organization_id)


class BackfillWeeksHandler:
    """The past weeks derived from the facts, so a trend exists before any screen draws it."""

    def __init__(self, snapshot: WeeklySnapshot):
        self.snapshot = snapshot

    def __call__(self, cmd: BackfillWeeks) -> int:
        return self.snapshot.backfill(cmd.organization_id)
