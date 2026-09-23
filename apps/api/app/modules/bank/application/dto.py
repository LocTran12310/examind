from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class BankFilters:
    """The bank's filters (subject-scoped-bank). `subject_id="none"` = questions without a subject; every chosen topic
    includes its subtree (several are OR-ed); tags: any of one group, every group; `school_year` is the source document's."""
    q: str = ""
    subject_id: uuid.UUID | str | None = None
    grade: int | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    type: str | None = None
    difficulty: str | None = None
    status: str | None = "usable"  # usable | all | a status
    topic_ids: tuple[uuid.UUID, ...] = ()
    tag_ids: tuple[uuid.UUID, ...] = ()
    document_id: uuid.UUID | None = None
    school_year: str | None = None
    has_topic: bool | None = None  # False = no row in question_topics (the tagging queue)


@dataclass(frozen=True)
class ResolvedFilters:
    """BankFilters with the taxonomy looked up: topic subtrees as ltree paths, tags grouped by their group."""
    filters: BankFilters
    topic_paths: tuple[str, ...] = ()
    tag_groups: tuple[tuple[uuid.UUID, ...], ...] = ()


@dataclass(frozen=True)
class TopicRefView:
    id: uuid.UUID
    name: str
    is_primary: bool
    source: str
    score: float | None


@dataclass(frozen=True)
class TopicSuggestionView:
    """A topic the classifier proposes for a question nobody placed (topic-coverage ADR-01); nothing is stored."""
    topic_id: uuid.UUID
    name: str
    path: str
    score: float
    source: str  # keyword | similar | ai


@dataclass(frozen=True)
class SuggestionsView:
    """What the tagging queue asked for: the candidates per question, and whether the tagging model was reached
    (topic-coverage AC-07 — a model that is off or slow only costs the `ai` candidates)."""
    by_question: dict[uuid.UUID, list[TopicSuggestionView]]
    model_used: bool


@dataclass(frozen=True)
class TagRefView:
    id: uuid.UUID
    group: str
    name: str


@dataclass(frozen=True)
class QuestionView:
    id: uuid.UUID
    type: str
    stem: str
    options: list[dict]
    answer: dict | None
    solution: str
    difficulty: str | None
    grade: int | None
    status: str
    number: int | None = None
    part: str | None = None
    confidence: float | None = None
    issues: list = field(default_factory=list)
    parse_method: str | None = None
    parse_model: str | None = None
    answer_source: str | None = None
    subject_id: uuid.UUID | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    topics: list[TopicRefView] = field(default_factory=list)
    tags: list[TagRefView] = field(default_factory=list)
    page: int | None = None
    spot_check: bool = False
    duplicate_of: uuid.UUID | None = None
    source_document_id: uuid.UUID | None = None
    group: str | None = None
    flag_evidence: dict | None = None


def question_view(q, topics=(), tags=(), group: str | None = None) -> QuestionView:
    return QuestionView(
        id=q.id, type=q.type, stem=q.stem, options=q.options or [], answer=q.answer, solution=q.solution, difficulty=q.difficulty,
        grade=q.grade, status=q.status, number=q.number, part=q.part, confidence=q.confidence, issues=q.issues or [],
        parse_method=q.parse_method, parse_model=q.parse_model, answer_source=q.answer_source, subject_id=q.subject_id,
        semester_code=q.semester_code, exam_kind=q.exam_kind, topics=list(topics), tags=list(tags), page=q.page,
        spot_check=q.spot_check, duplicate_of=q.duplicate_of, source_document_id=q.source_document_id, group=group,
        flag_evidence=q.flag_evidence,
    )


def student_view(q) -> QuestionView:
    """What a student may see outside an exam: no answer, no solution, no option marked true."""
    return QuestionView(id=q.id, type=q.type, stem=q.stem, options=[{k: v for k, v in o.items() if k != "is_true"} for o in q.options or []],
                        answer=None, solution="", difficulty=q.difficulty, grade=q.grade, status=q.status)


@dataclass(frozen=True)
class OptionStat:
    """One multiple-choice option and how many of the graded answers chose it."""
    label: str
    chosen: int
    ratio: float
    is_key: bool


@dataclass(frozen=True)
class ItemStats:
    """What the graded answers say about a question (learning-telemetry ADR-03). `enough_data` is false — and every
    number None — while the question has fewer than the minimum observations."""
    observations: int
    enough_data: bool = False
    correct_ratio: float | None = None
    first_attempt_ratio: float | None = None
    discrimination: float | None = None  # mean correct of the strongest third of the attempts minus the weakest third
    median_seconds: int | None = None
    options: list[OptionStat] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentRow:
    id: uuid.UUID
    filename: str
    mime: str
    size: int
    status: str
    error: str | None
    meta: dict
    processing_config: dict
    page_count: int | None
    question_count: int
    log: list
    created_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True)
class ReviewDocumentView:
    """A parsed document as the review list reads it: one state, how many questions still wait, and the breakdown
    behind them (review-ux ADR-01)."""
    document: DocumentRow
    total: int
    counts: dict[str, int]
    spot_pending: int
    pending: int
    review_state: str  # pending | in_progress | done
    progress: float
    assigned_to: uuid.UUID | None
    assigned_name: str | None


@dataclass(frozen=True)
class AnswerKeyResult:
    applied: int
    approved: int
    unmatched: list[int]


@dataclass(frozen=True)
class TriageCounts:
    auto_approved: int = 0
    needs_review: int = 0
    duplicate: int = 0
    spot_check: int = 0
