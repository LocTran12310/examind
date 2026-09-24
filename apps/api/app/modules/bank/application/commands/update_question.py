from dataclasses import dataclass
import uuid

from app.modules.bank.application.common import load_question, record, set_tags, set_topics, spot_feedback
from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, ReviewSettings, Taxonomy
from app.modules.bank.domain.services.review import check_grade, edit_content, set_difficulty, spot_check_failed_by_edit
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Invalid
from app.shared.domain.ids import new_id

CONTENT = frozenset({"stem", "options", "solution"})


@dataclass(frozen=True)
class UpdateQuestion:
    """None = unchanged. `sent` names the fields the client sent (an answer-only edit is recorded as "answer")."""
    question_id: uuid.UUID
    type: str | None = None
    stem: str | None = None
    options: list[dict] | None = None
    answer: dict | None = None
    solution: str | None = None
    difficulty: str | None = None
    grade: int | None = None
    subject_id: uuid.UUID | None = None
    topic_ids: list[uuid.UUID] | None = None
    primary_topic_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] | None = None
    sent: frozenset[str] = frozenset()


class UpdateQuestionHandler:
    """A teacher edits a question (bank page or review queue). The status stays: approval is explicit — except for a
    spot-checked question, whose correction counts as a failed check."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, settings: ReviewSettings,
                 views: QuestionViews, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.settings, self.views, self.uow = questions, taxonomy, log, settings, views, uow

    def __call__(self, actor: Actor, cmd: UpdateQuestion) -> QuestionView:
        batch = new_id()
        q = load_question(self.questions, actor.org_id, cmd.question_id)
        before = q.snapshot()
        was_spot = q.is_spot_pending
        changed = edit_content(q, type=cmd.type, stem=cmd.stem, solution=cmd.solution, options=cmd.options, answer=cmd.answer)
        if cmd.difficulty is not None:
            set_difficulty(q, cmd.difficulty)
        if cmd.grade is not None:
            q.grade = check_grade(cmd.grade, self.taxonomy.grade_levels(actor.org_id)) or None
        if cmd.subject_id is not None:
            if not self.taxonomy.subject_exists(actor.org_id, cmd.subject_id):
                raise Invalid("Môn học không hợp lệ", "subject_id")
            q.subject_id = cmd.subject_id
        if cmd.topic_ids is not None or cmd.primary_topic_id is not None:
            set_topics(self.questions, self.taxonomy, self.log, actor, q, cmd.topic_ids, cmd.primary_topic_id, batch)
        if cmd.tag_ids is not None:
            set_tags(self.questions, self.taxonomy, self.log, actor, q, cmd.tag_ids, batch)
        if was_spot and changed:
            spot_check_failed_by_edit(q, actor.user_id, utcnow())
            record(self.log, actor, q, "spot_fail", before, q.snapshot(), batch)
            spot_feedback(self.log, self.settings, actor, batch)
        else:
            action = "answer" if "answer" in cmd.sent and not (cmd.sent & CONTENT) else "edit"
            record(self.log, actor, q, action, before, q.snapshot(), batch)
        self.uow.commit()
        return self.views.views([q])[0]
