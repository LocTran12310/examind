"""Bank context: a question with its content, provenance and review state; its topic/tag links; the review history."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.ids import new_id

QUESTION_TYPES = ("mcq", "true_false", "short_answer", "essay")
STATUSES = ("draft", "auto_approved", "needs_review", "approved", "rejected", "duplicate", "flagged")
USABLE = ("auto_approved", "approved")
DIFFICULTIES = ("nb", "th", "vd", "vdc")
REVIEW_ACTIONS = ("approve", "reject", "restore", "edit", "answer", "topic", "skip", "spot_ok", "spot_fail", "bulk", "triage")
STATUS_KEYS = ("auto_approved", "needs_review", "approved", "rejected", "duplicate", "flagged")  # the review counts


@dataclass(eq=False)
class Question:
    """Full question content: stem, options, answer, solution — markdown + LaTeX + `asset:<id>` images."""
    organization_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    type: str = "mcq"
    stem: str = ""
    # mcq: [{label, content}], true_false: [{label, content, is_true}]
    options: list = field(default_factory=list)
    # mcq: {"key": "C"}; true_false: {"a": true, ...}; short_answer: {"value": "..."}; essay: {"text": "..."}
    answer: dict | None = None
    solution: str = ""
    difficulty: str | None = None
    grade: int | None = None
    status: str = "draft"
    source: str | None = None  # demo | document | manual
    source_document_id: uuid.UUID | None = None
    number: int | None = None
    page: int | None = None
    part: str | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    confidence: float | None = None
    issues: list = field(default_factory=list)
    parse_method: str | None = None
    parse_model: str | None = None
    answer_source: str | None = None
    duplicate_of: uuid.UUID | None = None
    search_text: str = ""
    spot_check: bool = False
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    updated_at: datetime | None = None
    flag_evidence: dict | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def is_spot_pending(self) -> bool:
        """An auto-approved question drawn for a random check that nobody looked at yet."""
        return bool(self.spot_check) and self.status == "auto_approved"

    def snapshot(self) -> dict:
        """What a review event records before/after a change."""
        return {"status": self.status, "answer": self.answer, "confidence": self.confidence, "issues": list(self.issues or [])}

    def mark_reviewed(self, user_id: uuid.UUID, when: datetime) -> None:
        self.reviewed_by, self.reviewed_at = user_id, when


@dataclass(eq=False)
class QuestionTopic:
    """A question placed in a node of the knowledge tree; one link per question is the primary one."""
    question_id: uuid.UUID
    topic_id: uuid.UUID
    is_primary: bool = False
    source: str = "manual"  # auto | ai | manual
    score: float | None = None


@dataclass(eq=False)
class QuestionTag:
    question_id: uuid.UUID
    tag_id: uuid.UUID


@dataclass(eq=False)
class ReviewEvent:
    """Append-only history of review actions (question-review ADR-03). Never updated."""
    organization_id: uuid.UUID
    action: str
    question_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    before: dict | None = None
    after: dict | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None
