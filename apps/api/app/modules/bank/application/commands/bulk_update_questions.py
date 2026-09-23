from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import record, set_tags, set_topics
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, Taxonomy
from app.modules.bank.domain.services.quality import blocking_manual, settle
from app.modules.bank.domain.services.review import blocking_message, check_difficulty
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Conflict, Invalid, NotFound

BULK_STATUSES = ("approved", "rejected", "needs_review")


@dataclass(frozen=True)
class BulkUpdateQuestions:
    ids: list[uuid.UUID]
    status: str | None = None  # approved | rejected | needs_review (a decision taken back)
    difficulty: str | None = None
    primary_topic_id: uuid.UUID | None = None
    add_tag_ids: list[uuid.UUID] | None = None


class BulkUpdateQuestionsHandler:
    """The bank's bulk bar: approve / reject / send back for review, difficulty, primary topic, add tags — all or
    nothing. Sending back is how a decision is taken back (review-ux ADR-02): the same command, no undo stack."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.uow = questions, taxonomy, log, uow

    def __call__(self, actor: Actor, cmd: BulkUpdateQuestions) -> int:
        qs = self.questions.many(actor.org_id, list(cmd.ids))
        if len(qs) != len(set(cmd.ids)):
            raise NotFound("Một số câu hỏi không tồn tại")
        if cmd.status and cmd.status not in BULK_STATUSES:
            raise Invalid("Chỉ có thể duyệt, loại hoặc trả lại để xem hàng loạt", "status")
        check_difficulty(cmd.difficulty)
        now = utcnow()
        for q in qs:
            before = q.snapshot()
            if cmd.difficulty:
                q.difficulty = cmd.difficulty
            if cmd.primary_topic_id:
                set_topics(self.questions, self.taxonomy, self.log, actor, q, None, cmd.primary_topic_id)
            if cmd.add_tag_ids:
                set_tags(self.questions, self.taxonomy, actor, q, list(self.questions.tag_ids(q.id) | set(cmd.add_tag_ids)))
            if cmd.status == "approved":
                if blocking_manual(q.issues or []):
                    raise Conflict(blocking_message(q, f"Câu {q.number or ''}"), code="has_blocking_issues")
                settle(q)
                q.status, q.spot_check = "approved", False
                q.mark_reviewed(actor.user_id, now)
            elif cmd.status == "rejected":
                q.status, q.spot_check = "rejected", False
            elif cmd.status == "needs_review":  # a decision taken back: the question goes back on a teacher's desk
                q.status, q.spot_check = "needs_review", False
            record(self.log, actor, q, "bulk", before, q.snapshot())
        self.uow.commit()
        return len(qs)
