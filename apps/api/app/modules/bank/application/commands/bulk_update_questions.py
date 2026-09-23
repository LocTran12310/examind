from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import record, set_tags, set_topics
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, Taxonomy
from app.modules.bank.domain.services.quality import blocking_manual, settle
from app.modules.bank.domain.services.review import blocking_message, check_difficulty, check_grade
from app.modules.bank.domain.services.tagging import check_subject_change
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Conflict, Invalid, NotFound
from app.shared.domain.ids import new_id

BULK_STATUSES = ("approved", "rejected", "needs_review")


@dataclass(frozen=True)
class BulkUpdateQuestions:
    ids: list[uuid.UUID]
    status: str | None = None  # approved | rejected | needs_review (a decision taken back)
    difficulty: str | None = None
    primary_topic_id: uuid.UUID | None = None
    add_tag_ids: list[uuid.UUID] | None = None
    subject_id: uuid.UUID | None = None
    grade: int | None = None


class BulkUpdateQuestionsHandler:
    """The bank's bulk bar: approve / reject / send back for review, difficulty, primary topic, add tags, subject and
    grade — all or nothing. Sending back is how a decision is taken back (review-ux ADR-02): the same command, no undo
    stack. Subject and grade are checked exactly as a single edit checks them (A-04)."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.uow = questions, taxonomy, log, uow

    def __call__(self, actor: Actor, cmd: BulkUpdateQuestions) -> int:
        qs = self.questions.many(actor.org_id, list(cmd.ids))
        if len(qs) != len(set(cmd.ids)):
            raise NotFound("Một số câu hỏi không tồn tại")
        if cmd.status and cmd.status not in BULK_STATUSES:
            raise Invalid("Chỉ có thể duyệt, loại hoặc trả lại để xem hàng loạt", "status")
        check_difficulty(cmd.difficulty)
        if cmd.grade is not None:
            check_grade(cmd.grade, self.taxonomy.grade_levels(actor.org_id))
        if cmd.subject_id is not None:
            if not self.taxonomy.subject_exists(actor.org_id, cmd.subject_id):
                raise Invalid("Môn học không hợp lệ", "subject_id")
            self._guard_topics(actor, cmd, qs)
        now, batch = utcnow(), new_id()  # every event of this request shares one batch: the bar's edit is one unit
        for q in qs:
            # the whole state the bar can move, read before anything is touched: one event is enough to put the
            # question back, without reading the finer topic/tag events of the same batch
            topics, primary = self.questions.topic_ids(q.id)
            tags = self.questions.tag_ids(q.id)
            before = q.snapshot(topics, primary, list(tags))
            if cmd.difficulty:
                q.difficulty = cmd.difficulty
            if cmd.grade is not None:
                q.grade = cmd.grade or None
            if cmd.subject_id:
                q.subject_id = cmd.subject_id
            if cmd.primary_topic_id:
                set_topics(self.questions, self.taxonomy, self.log, actor, q, None, cmd.primary_topic_id, batch)
                topics, primary = [cmd.primary_topic_id], cmd.primary_topic_id
            if cmd.add_tag_ids:
                tags = tags | set(cmd.add_tag_ids)
                set_tags(self.questions, self.taxonomy, self.log, actor, q, list(tags), batch)
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
            record(self.log, actor, q, "bulk", before, q.snapshot(topics, primary, list(tags)), batch)
        self.uow.commit()
        return len(qs)

    def _guard_topics(self, actor: Actor, cmd: BulkUpdateQuestions, qs: list) -> None:
        """A new subject may not leave a question in another subject's tree: the whole edit is refused, naming the
        questions and the topics in the way (A-04)."""
        placed = ({q.id: cmd.primary_topic_id for q in qs} if cmd.primary_topic_id
                  else self.questions.primary_topic_ids([q.id for q in qs]))
        topic_ids = list(dict.fromkeys(placed.values()))
        subject_of = self.taxonomy.topic_subjects(actor.org_id, topic_ids)
        labels = self.taxonomy.topic_labels(actor.org_id, topic_ids)
        check_subject_change(cmd.subject_id, {qid: (tid, subject_of.get(tid), labels.get(tid, ("", ""))[0])
                                              for qid, tid in placed.items()})
