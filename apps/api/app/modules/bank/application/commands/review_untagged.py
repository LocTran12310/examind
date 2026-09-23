from dataclasses import dataclass
import uuid

from app.modules.bank.domain.ports import QuestionRepository
from app.modules.bank.domain.services.triage import waits_for_a_topic
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ReviewUntagged:
    question_ids: list[uuid.UUID]


class ReviewUntaggedHandler:
    """Freshly parsed questions the classifier could not place (topic-coverage ADR-02, A-02): they wait for a teacher
    instead of being auto-approved. Flushed, not committed: the ingestion pipeline owns the transaction."""

    def __init__(self, questions: QuestionRepository, uow: UnitOfWork):
        self.questions, self.uow = questions, uow

    def __call__(self, cmd: ReviewUntagged) -> int:
        moved = [q for q in self.questions.many(None, list(cmd.question_ids)) if waits_for_a_topic(q)]
        for q in moved:
            q.status = "needs_review"
            q.spot_check = False  # it was drawn as a sample of auto-approval; a teacher now looks at it anyway
        self.uow.flush()
        return len(moved)
