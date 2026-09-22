"""What other contexts, the worker and the bootstrap may ask analytics (architecture-refactor ADR-01)."""
from datetime import datetime
import uuid

from app.modules.analytics.application.commands.rebuild_mastery import RebuildMastery, RebuildMasteryHandler
from app.modules.analytics.application.commands.record_answer import RecordAnswer, RecordAnswerHandler
from app.modules.analytics.domain.ports import AnswerHistory, MasteryRepository, Topics
from app.modules.analytics.domain.value_objects import AnswerRecord
from app.shared.application.unit_of_work import UnitOfWork


class AnalyticsApi:
    def __init__(self, mastery: MasteryRepository, topics: Topics, history: AnswerHistory, uow: UnitOfWork):
        self.mastery, self.topics, self.history, self.uow = mastery, topics, history, uow

    def answer_recorded(self, org_id: uuid.UUID, student_id: uuid.UUID, topic_path: str | None, correct_ratio: float,
                        difficulty: str | None, at: datetime | None) -> None:
        """Assessment graded an answer (its answer fact): the topic mastery follows, in the grading transaction."""
        RecordAnswerHandler(self.mastery, self.topics, self.uow)(
            RecordAnswer(AnswerRecord(org_id, student_id, topic_path, correct_ratio, difficulty, at)))

    def rebuild_mastery(self, org_id: uuid.UUID | None = None) -> int:
        """Mastery replayed from every answer fact (of the org when given); flushed, the caller commits."""
        return RebuildMasteryHandler(self.mastery, self.topics, self.history, self.uow)(RebuildMastery(org_id))

    def rebuild_mastery_if_missing(self) -> int:
        """Answers graded before mastery tracking existed (adaptive-review AC-03): replayed once, when no mastery is kept yet."""
        if self.mastery.empty() and not self.history.empty():
            return self.rebuild_mastery()
        return 0
