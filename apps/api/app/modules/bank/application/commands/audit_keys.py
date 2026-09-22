from dataclasses import dataclass
import uuid

from app.modules.bank.domain.ports import AnswerStats, QuestionRepository, ReviewLog
from app.modules.bank.domain.services.key_audit import audit_question
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AuditKeys:
    org_id: uuid.UUID | None = None  # None = every organisation (the worker's periodic run)


class AuditKeysHandler:
    """Flag usable MCQs whose answers contradict their key (adaptive-review ADR-03); they leave the pool until reviewed.
    Flushed, not committed: the endpoint commits, the worker commits its own session."""

    def __init__(self, questions: QuestionRepository, stats: AnswerStats, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.stats, self.log, self.uow = questions, stats, log, uow

    def __call__(self, cmd: AuditKeys) -> list[uuid.UUID]:
        answers = self.stats.mcq_answers(cmd.org_id)
        by_id = {q.id: q for q in self.questions.many(cmd.org_id, list(answers))}
        flagged = []
        for qid, rows in answers.items():
            q = by_id.get(qid)
            if q is None:
                continue
            ev = audit_question(q, rows)
            if ev is None:
                continue
            self.log.record(q.organization_id, None, q.id, "triage", {"status": "usable"}, {"status": "flagged", "reason": ev["reason"]})
            flagged.append(q.id)
        self.uow.flush()
        return flagged
