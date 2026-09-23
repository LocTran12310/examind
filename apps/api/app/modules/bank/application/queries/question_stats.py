from dataclasses import dataclass, replace
import uuid

from app.modules.bank.application.common import load_question
from app.modules.bank.application.dto import ItemStats
from app.modules.bank.application.ports import ItemStatsReader
from app.modules.bank.domain.ports import QuestionRepository
from app.modules.bank.domain.services.item_stats import enough
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class QuestionStats:
    question_id: uuid.UUID


class QuestionStatsHandler:
    """What the graded answers say about one question. A question of another organisation is not found; below the
    minimum number of observations only the count is reported (learning-telemetry ADR-03, A-05)."""

    def __init__(self, questions: QuestionRepository, stats: ItemStatsReader):
        self.questions, self.stats = questions, stats

    def __call__(self, actor: Actor, query: QuestionStats) -> ItemStats:
        q = load_question(self.questions, actor.org_id, query.question_id)
        measured = self.stats.stats(actor.org_id, q)
        if not enough(measured.observations):
            return ItemStats(observations=measured.observations)
        return replace(measured, enough_data=True)
