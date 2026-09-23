from dataclasses import dataclass, field
import uuid

from app.modules.bank.application.common import record, set_tags, set_topics
from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.ports import QuestionRepository, ReviewLog, Taxonomy
from app.modules.bank.domain.services.quality import blocking, evaluate
from app.modules.bank.domain.services.review import check_difficulty, check_type, valid_answer
from app.modules.bank.domain.services.search_text import for_question
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Invalid
from app.shared.domain.ids import new_id


@dataclass(frozen=True)
class CreateQuestion:
    type: str | None = None
    stem: str = ""
    options: list[dict] = field(default_factory=list)
    answer: dict | None = None
    solution: str = ""
    difficulty: str | None = None
    grade: int | None = None
    subject_id: uuid.UUID | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    topic_ids: list[uuid.UUID] | None = None
    primary_topic_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] | None = None


class CreateQuestionHandler:
    """A teacher writes a question by hand: it is approved at once when it has no blocking issue."""

    def __init__(self, questions: QuestionRepository, taxonomy: Taxonomy, log: ReviewLog, views: QuestionViews, uow: UnitOfWork):
        self.questions, self.taxonomy, self.log, self.views, self.uow = questions, taxonomy, log, views, uow

    def __call__(self, actor: Actor, cmd: CreateQuestion) -> QuestionView:
        batch = new_id()  # one request, one batch — a single edit is a batch of one (bulk-safety ADR-01)
        qtype = check_type(cmd.type or "mcq")
        q = Question(organization_id=actor.org_id, type=qtype, stem=cmd.stem or "", options=cmd.options or [], solution=cmd.solution or "",
                     difficulty=check_difficulty(cmd.difficulty), grade=cmd.grade, subject_id=cmd.subject_id,
                     semester_code=cmd.semester_code, exam_kind=cmd.exam_kind, source="manual", status="approved", issues=[],
                     answer_source="manual")
        if cmd.answer:
            q.answer = valid_answer(q.type, q.options, cmd.answer)
        q.issues, q.confidence = evaluate(q.type, q.stem, q.options, q.answer, q.solution)
        if blocking(q.issues):
            raise Invalid("Câu còn lỗi: " + ", ".join(blocking(q.issues)), code="has_blocking_issues")
        q.search_text = for_question(q.stem, q.options)
        q.mark_reviewed(actor.user_id, utcnow())
        self.questions.add(q)
        if cmd.primary_topic_id or cmd.topic_ids:
            set_topics(self.questions, self.taxonomy, self.log, actor, q, cmd.topic_ids, cmd.primary_topic_id, batch)
        if cmd.tag_ids:
            set_tags(self.questions, self.taxonomy, self.log, actor, q, cmd.tag_ids, batch)
        record(self.log, actor, q, "edit", None, q.snapshot(), batch)
        self.uow.commit()
        return self.views.views([q])[0]
