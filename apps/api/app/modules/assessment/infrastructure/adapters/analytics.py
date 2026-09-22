"""FactListener over the analytics context's application API (topic mastery), handed in by the composition root:
assessment never imports another module."""
from datetime import datetime
from typing import Protocol
import uuid

from app.modules.assessment.domain.entities import AnswerFact


class _AnalyticsApi(Protocol):
    def answer_recorded(self, org_id: uuid.UUID, student_id: uuid.UUID, topic_path: str | None, correct_ratio: float,
                        difficulty: str | None, at: datetime | None) -> None: ...


class AnalyticsFactListener:
    def __init__(self, analytics: _AnalyticsApi):
        self.analytics = analytics

    def recorded(self, fact: AnswerFact) -> None:
        self.analytics.answer_recorded(fact.organization_id, fact.student_id, fact.topic_path, fact.correct_ratio, fact.difficulty,
                                       fact.created_at)
