"""Analytics context: how well each student masters each topic (adaptive-review US-01, ADR-01), what the reports
show over the graded answer facts, and the personal review exams built from both (US-02, US-03)."""
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass(eq=False)
class TopicMastery:
    """A student's mastery (0..1) of one leaf topic: a difficulty-weighted moving average of their answers."""
    student_id: uuid.UUID
    topic_id: uuid.UUID
    organization_id: uuid.UUID
    mastery: float
    answers: int = 0
    last_at: datetime | None = None
