from dataclasses import dataclass, field
import uuid

from app.modules.bank.application.common import record, set_topics
from app.modules.bank.application.dto import BulkTopicsResult, SkippedPair
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, Taxonomy
from app.modules.bank.domain.services.tagging import SKIP_REASONS, check_pairs, pair_skip
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.ids import new_id


@dataclass(frozen=True)
class BulkSetTopics:
    pairs: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)  # (question_id, topic_id)


class BulkSetTopicsHandler:
    """A page of the tagging queue in one request (ADR-02): each question takes its own topic as primary, with
    `source = manual` — a teacher confirmed it, even when the value came from a suggestion. One transaction; the
    pairs it cannot apply are reported instead of failing the others."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.uow = questions, taxonomy, log, uow

    def __call__(self, actor: Actor, cmd: BulkSetTopics) -> BulkTopicsResult:
        batch = new_id()
        pairs = [(q, t) for q, t in cmd.pairs]
        check_pairs(len(pairs))
        mine = {q.id: q for q in self.questions.many(actor.org_id, [q for q, _ in pairs])}
        missing = [q for q, _ in pairs if q not in mine]
        elsewhere = {q.id for q in self.questions.many(None, missing)} if missing else set()
        subject_of = self.taxonomy.topic_subjects(actor.org_id, [t for _, t in pairs])
        updated, skipped = 0, []
        for question_id, topic_id in pairs:
            q = mine.get(question_id)
            reason = ("other_org" if question_id in elsewhere else "unknown_question") if q is None \
                else pair_skip(q.subject_id, subject_of.get(topic_id))
            if reason:
                skipped.append(SkippedPair(question_id, topic_id, reason, SKIP_REASONS[reason]))
                continue
            set_topics(self.questions, self.taxonomy, self.log, actor, q, None, topic_id, batch)
            updated += 1
        record(self.log, actor, None, "bulk", None, {"pairs": len(pairs), "updated": updated, "skipped": len(skipped)}, batch)
        self.uow.commit()
        return BulkTopicsResult(updated, skipped, batch)
