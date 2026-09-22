from dataclasses import dataclass

from app.modules.bank.application.dto import TriageCounts
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import DuplicateFinder
from app.modules.bank.domain.services.quality import triage_status
from app.modules.bank.domain.services.search_text import for_question
from app.modules.bank.domain.services.triage import MIN_DUPLICATE_TEXT, is_duplicate, spot_sample
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class TriageQuestions:
    questions: list[Question]
    threshold: float
    seed: str = ""


class TriageQuestionsHandler:
    """Freshly parsed questions (US-01, A-02, A-03, A-07): search text, near-duplicates of usable questions from other
    documents, auto-approve vs review, and a reproducible 5% spot check of the auto-approved ones.
    Flushed, not committed: the ingestion pipeline owns the transaction."""

    def __init__(self, duplicates: DuplicateFinder, uow: UnitOfWork):
        self.duplicates, self.uow = duplicates, uow

    def __call__(self, cmd: TriageQuestions) -> TriageCounts:
        counts = {"auto_approved": 0, "needs_review": 0, "duplicate": 0, "spot_check": 0}
        auto: list[Question] = []
        for q in cmd.questions:
            q.search_text = for_question(q.stem, q.options)
        self.uow.flush()
        for q in cmd.questions:
            dup = self._duplicate_of(q)
            if dup is not None:
                q.status, q.duplicate_of = "duplicate", dup
                counts["duplicate"] += 1
                continue
            q.status = triage_status(q.confidence, q.issues or [], cmd.threshold)
            counts[q.status] += 1
            if q.status == "auto_approved":
                auto.append(q)
        spots = spot_sample(auto, cmd.seed)
        for q in spots:
            q.spot_check = True
        counts["spot_check"] = len(spots)
        self.uow.flush()
        return TriageCounts(**counts)

    def _duplicate_of(self, q: Question):
        if len(q.search_text) < MIN_DUPLICATE_TEXT:
            return None
        for qid, similarity, text in self.duplicates.similar(q):
            if is_duplicate(q, text, similarity):
                return qid
        return None
