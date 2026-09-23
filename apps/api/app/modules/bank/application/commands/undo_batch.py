from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import record, set_tags, set_topics
from app.modules.bank.application.dto import UndoResult
from app.modules.bank.domain.entities import STATUSES
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, Taxonomy
from app.modules.bank.domain.services.history import BLOCKED, UNDONE_BATCH, batch_action, lost_question, restore_targets, undo_block
from app.modules.bank.domain.services.review import check_difficulty, check_grade
from app.modules.bank.domain.services.tagging import check_subject_change
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Conflict, Invalid, NotFound
from app.shared.domain.ids import new_id


@dataclass(frozen=True)
class UndoBatch:
    batch_id: uuid.UUID


class UndoBatchHandler:
    """"Hoàn tác": one recorded change put back as one unit (AC-01). The `before` its events kept is written through
    the same aggregate and the same guards a manual edit runs (ADR-04) — a restore that skipped them could leave a
    question in another subject's tree, the very state `subject_topic_conflict` exists to prevent. All or nothing
    (AC-02): a question that is gone, or a guard that refuses, stops the batch before anything is written. The
    restore is itself recorded, under a new batch naming the one it took back, which is what a second undo runs
    into (A-04) — and what the history list reads to mark the original as already undone."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.uow = questions, taxonomy, log, uow

    def __call__(self, actor: Actor, cmd: UndoBatch) -> UndoResult:
        events = self.log.batch(actor.org_id, cmd.batch_id)
        if not events:
            raise NotFound("Không tìm thấy lượt sửa này", code="batch_not_found")
        self._check_undoable(actor, cmd, events)
        targets = restore_targets(events)
        qs = {q.id: q for q in self.questions.many(actor.org_id, list(targets))}
        gone = sorted(str(qid) for qid in targets if qid not in qs)
        if gone or any(lost_question(e) for e in events):
            message = (f"{len(gone)} câu trong lượt sửa này không còn nữa nên không hoàn tác được" if gone
                       else "Một số câu trong lượt sửa này đã bị xóa nên không hoàn tác được")
            raise Invalid(message, code="questions_gone", fields={"batch_id": message, "question_ids": gone})
        self._guard_subjects(actor, targets)
        batch, levels = new_id(), self.taxonomy.grade_levels(actor.org_id)
        for question_id, target in targets.items():
            self._restore(actor, qs[question_id], target, levels, cmd.batch_id, batch)
        # the batch names what it took back even when the recorded change left nothing to restore (a tagging request
        # whose pairs were all skipped): without this row the undo would not be in the history at all
        record(self.log, actor, None, "undo", None, {UNDONE_BATCH: str(cmd.batch_id), "questions": len(targets)}, batch)
        self.uow.commit()
        return UndoResult(restored=len(targets), batch_id=batch)

    def _check_undoable(self, actor: Actor, cmd: UndoBatch, events: list) -> None:
        """The three refusals the history list shows as a reason (AC-04, AC-05), raised here as errors: the batch was
        already taken back, it is itself an undo, or it is past the window — the most specific one wins."""
        now = utcnow()
        created = min((e.created_at for e in events if e.created_at), default=None)
        undone_by = self.log.undone_by(actor.org_id, cmd.batch_id)
        blocked = undo_block(True, batch_action(e.action for e in events), created, now, undone_by is not None)
        if blocked == "already_undone":
            raise Conflict(BLOCKED[blocked], code="batch_already_undone", fields={"undone_by": str(undone_by)})
        if blocked == "is_undo":
            raise Conflict(BLOCKED[blocked], code="batch_is_undo", fields={"batch_id": BLOCKED[blocked]})
        if blocked == "expired":
            raise Invalid(BLOCKED[blocked], code="batch_expired",
                          fields={"batch_id": BLOCKED[blocked], "age_days": (now - created).days})

    def _guard_subjects(self, actor: Actor, targets: dict) -> None:
        """A restored subject may not leave a question in another subject's tree: the check a bulk subject change
        makes, run once per subject the batch puts back and before anything is written. The topic to weigh is the one
        the restore ends with — the recorded placement when the batch moved it, the current one otherwise."""
        current = self.questions.primary_topic_ids(list(targets))
        placed: dict[uuid.UUID, dict] = {}
        for question_id, target in targets.items():
            subject = _uuid(target.get("subject_id"))
            primary = _uuid(target["primary_topic"]) if "primary_topic" in target else current.get(question_id)
            if subject is not None and primary is not None:
                placed.setdefault(subject, {})[question_id] = primary
        topic_ids = list(dict.fromkeys(t for by_question in placed.values() for t in by_question.values()))
        subject_of = self.taxonomy.topic_subjects(actor.org_id, topic_ids)
        labels = self.taxonomy.topic_labels(actor.org_id, topic_ids)
        for subject in sorted(placed, key=str):
            check_subject_change(subject, {qid: (tid, subject_of.get(tid), labels.get(tid, ("", ""))[0])
                                           for qid, tid in placed[subject].items()})

    def _restore(self, actor: Actor, q, target: dict, levels: set[int], undone: uuid.UUID, batch: uuid.UUID) -> None:
        """One question back to its recorded state, field by field, through the checks an edit goes through. A field
        the snapshot does not mention is left alone: the batch never moved it, so the undo has nothing to say about it."""
        topics, primary = self.questions.topic_ids(q.id)
        tags = self.questions.tag_ids(q.id)
        before = q.snapshot(topics, primary, list(tags))
        if "status" in target:
            if target["status"] not in STATUSES:
                raise Invalid("Trạng thái không hợp lệ", "status")
            q.status = target["status"]
        if "difficulty" in target:
            q.difficulty = check_difficulty(target["difficulty"])
        if "grade" in target:
            q.grade = check_grade(target["grade"], levels) or None
        if "subject_id" in target:
            subject = _uuid(target["subject_id"])
            if subject is not None and not self.taxonomy.subject_exists(actor.org_id, subject):
                raise Invalid("Môn học không hợp lệ", "subject_id")
            q.subject_id = subject
        # a placement or a tag set the batch did not actually move is left untouched: rewriting it would replace the
        # links, and with them how the question got there (a suggestion the classifier scored would come back as a
        # teacher's own manual placement) — an undo puts the state back, it does not restate it
        if "topics" in target:
            want, want_primary = [_uuid(t) for t in target["topics"]], _uuid(target.get("primary_topic"))
            if (set(want), want_primary) != (set(topics), primary):
                set_topics(self.questions, self.taxonomy, self.log, actor, q, want, want_primary, batch)
                topics, primary = want, want_primary
        if "tags" in target:
            want_tags = {_uuid(t) for t in target["tags"]}
            if want_tags != tags:
                set_tags(self.questions, self.taxonomy, self.log, actor, q, list(want_tags), batch)
                tags = want_tags
        after = {**q.snapshot(topics, primary, list(tags)), UNDONE_BATCH: str(undone)}
        record(self.log, actor, q, "undo", before, after, batch)


def _uuid(value) -> uuid.UUID | None:
    """A snapshot keeps ids as strings (JSONB has no uuid); an absent or empty one is "nothing there"."""
    return uuid.UUID(value) if value else None
