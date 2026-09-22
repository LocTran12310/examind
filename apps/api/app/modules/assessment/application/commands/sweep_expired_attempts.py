from app.modules.assessment.application.common import Clock, Grading
from app.modules.assessment.domain.ports import AttemptRepository
from app.modules.assessment.domain.services.attempt_rules import GRACE


class SweepExpiredAttemptsHandler:
    """The worker closes abandoned attempts past their deadline (plus grace); flushed, the worker commits."""

    def __init__(self, attempts: AttemptRepository, grading: Grading, clock: Clock):
        self.attempts, self.grading, self.clock = attempts, grading, clock

    def __call__(self) -> int:
        rows = self.attempts.expired(self.clock() - GRACE)
        for att in rows:
            self.grading.submit(att, auto=True)
        return len(rows)
