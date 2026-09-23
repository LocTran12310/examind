"""What other contexts, the worker and the bootstrap may ask analytics (architecture-refactor ADR-01)."""
from datetime import date, datetime
import uuid

from app.modules.analytics.application.commands.rebuild_mastery import replay
from app.modules.analytics.application.commands.record_answer import RecordAnswer, RecordAnswerHandler
from app.modules.analytics.application.commands.snapshot_week import (
    BackfillWeeks,
    BackfillWeeksHandler,
    SnapshotWeek,
    SnapshotWeekHandler,
    WeeklySnapshot,
)
from app.modules.analytics.application.common import Clock
from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, Topics, WeekRepository
from app.modules.analytics.domain.value_objects import AnswerRecord
from app.shared.application.calendar import BusinessCalendar
from app.shared.application.unit_of_work import UnitOfWork


class AnalyticsApi:
    def __init__(self, mastery: MasteryRepository, topics: Topics, history: AnswerHistory, weeks: WeekRepository,
                 cal: BusinessCalendar, clock: Clock, uow: UnitOfWork):
        self.mastery, self.topics, self.history, self.weeks = mastery, topics, history, weeks
        self.cal, self.clock, self.uow = cal, clock, uow

    def answer_recorded(self, org_id: uuid.UUID, student_id: uuid.UUID, topic_path: str | None, correct_ratio: float,
                        difficulty: str | None, at: datetime | None) -> None:
        """Assessment graded an answer (its answer fact): the topic mastery follows, in the grading transaction."""
        RecordAnswerHandler(self.mastery, self.topics, self.uow)(
            RecordAnswer(AnswerRecord(org_id, student_id, topic_path, correct_ratio, difficulty, at)))

    def rebuild_mastery(self, org_id: uuid.UUID | None = None) -> int:
        """Mastery replayed from every answer fact (of the org when given); flushed, the caller commits. Returns the
        facts replayed — an org admin calls the endpoint instead and gets the students and topics too."""
        return replay(self.mastery, self.topics, self.history, self.uow, org_id).facts

    def rebuild_mastery_if_missing(self) -> int:
        """Answers graded before mastery tracking existed (adaptive-review AC-03): replayed once, when no mastery is kept yet."""
        if self.mastery.empty() and not self.history.empty():
            return self.rebuild_mastery()
        return 0

    def _snapshot(self) -> WeeklySnapshot:
        return WeeklySnapshot(self.weeks, self.topics, self.history, self.cal, self.clock, self.uow)

    def snapshot_mastery_week(self, week_start: date | None = None) -> int:
        """The weekly mastery snapshot of the running business week (the worker's job); rows written."""
        return SnapshotWeekHandler(self._snapshot(), self.cal)(SnapshotWeek(week_start))

    def backfill_mastery_weeks_if_missing(self) -> int:
        """The past weeks derived from the facts, once, while no snapshot is kept yet (learning-telemetry A-06)."""
        if self.weeks.empty() and not self.history.empty():
            return BackfillWeeksHandler(self._snapshot())(BackfillWeeks())
        return 0
