from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel

from app.modules.bank.application.dto import BankFilters, ItemStats, QuestionView, ReviewDocumentView
from app.shared.domain.errors import Invalid
from app.shared.interface.search_schemas import SearchBody


class QuestionOut(BaseModel):
    id: uuid.UUID
    type: str
    stem: str
    options: list[dict]
    answer: dict | None
    solution: str
    difficulty: str | None
    grade: int | None
    status: str


def question_out(q, hide_answer: bool = False) -> QuestionOut:
    """A question (entity or view) without provenance; `hide_answer` for students outside a finished exam."""
    options = q.options or []
    if hide_answer:
        options = [{k: v for k, v in o.items() if k != "is_true"} for o in options]
    return QuestionOut(id=q.id, type=q.type, stem=q.stem, options=options,
                       answer=None if hide_answer else q.answer, solution="" if hide_answer else q.solution,
                       difficulty=q.difficulty, grade=q.grade, status=q.status)


class TopicRef(BaseModel):
    id: uuid.UUID
    name: str
    is_primary: bool
    source: str
    score: float | None


class TagRef(BaseModel):
    id: uuid.UUID
    group: str
    name: str


class ParsedQuestionOut(QuestionOut):
    number: int | None
    part: str | None
    confidence: float | None
    issues: list
    parse_method: str | None
    parse_model: str | None
    answer_source: str | None
    subject_id: uuid.UUID | None
    semester_code: str | None
    exam_kind: str | None
    topics: list[TopicRef] = []
    tags: list[TagRef] = []
    page: int | None = None
    spot_check: bool = False
    duplicate_of: uuid.UUID | None = None
    source_document_id: uuid.UUID | None = None
    group: str | None = None
    flag_evidence: dict | None = None


def parsed_out(v: QuestionView) -> ParsedQuestionOut:
    return ParsedQuestionOut(**{**vars(v), "topics": [TopicRef(**vars(t)) for t in v.topics], "tags": [TagRef(**vars(t)) for t in v.tags]})


class QuestionCreate(BaseModel):
    type: str | None = None
    stem: str | None = None
    options: list[dict] | None = None
    answer: Any = None
    solution: str | None = None
    difficulty: str | None = None
    grade: int | None = None
    subject_id: uuid.UUID | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    topic_ids: list[uuid.UUID] | None = None
    primary_topic_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] | None = None


class QuestionPatch(BaseModel):
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


class BulkSet(BaseModel):
    status: str | None = None  # approved | rejected
    difficulty: str | None = None
    primary_topic_id: uuid.UUID | None = None
    add_tag_ids: list[uuid.UUID] | None = None


class BulkIn(BaseModel):
    ids: list[uuid.UUID] = []
    set: BulkSet = BulkSet()


class BulkOut(BaseModel):
    updated: int


class ActionIn(BaseModel):
    action: str


class SuggestTopicsIn(BaseModel):
    question_ids: list[uuid.UUID] = []


class TopicSuggestionOut(BaseModel):
    topic_id: uuid.UUID
    name: str
    path: str
    score: float
    source: str


class SuggestionsOut(BaseModel):
    suggestions: dict[uuid.UUID, list[TopicSuggestionOut]]


class QuestionSearchBody(SearchBody):
    """The bank's filters sit at the top of the body: `subject_id` a subject id or "none" (no subject);
    `topic_id` / `topic_ids` include each node's subtree (OR); `tag_ids` any of one group, every group;
    `status` "usable" (default), "all" or a status; `school_year` of the source document;
    `has_topic` false = the questions nobody placed in the topic tree."""
    has_topic: bool | None = None
    subject_id: str | None = None
    grade: int | None = None
    semester_code: str | None = None
    exam_kind: str | None = None
    type: str | None = None
    difficulty: str | None = None
    status: str | None = "usable"
    topic_id: uuid.UUID | None = None
    topic_ids: list[uuid.UUID] = []
    tag_ids: list[uuid.UUID] = []
    document_id: uuid.UUID | None = None
    school_year: str | None = None

    def to_filters(self) -> BankFilters:
        subject: uuid.UUID | str | None = None
        if self.subject_id == "none":
            subject = "none"
        elif self.subject_id:
            try:
                subject = uuid.UUID(self.subject_id)
            except ValueError:
                raise Invalid("Môn học không hợp lệ", "subject_id") from None
        topics = tuple(dict.fromkeys([t for t in [self.topic_id, *self.topic_ids] if t]))
        return BankFilters(q=self.q.strip(), subject_id=subject, grade=self.grade, semester_code=self.semester_code or None,
                           exam_kind=self.exam_kind or None, type=self.type or None, difficulty=self.difficulty or None,
                           status=self.status, topic_ids=topics, tag_ids=tuple(dict.fromkeys(self.tag_ids)),
                           document_id=self.document_id, school_year=self.school_year or None, has_topic=self.has_topic)


class OptionStatOut(BaseModel):
    label: str
    chosen: int
    ratio: float
    is_key: bool


class QuestionStatsOut(BaseModel):
    """Item statistics of one question; every number is null while `enough_data` is false (ADR-03)."""
    observations: int
    enough_data: bool
    correct_ratio: float | None
    first_attempt_ratio: float | None
    discrimination: float | None
    median_seconds: int | None
    options: list[OptionStatOut] = []


def question_stats_out(s: ItemStats) -> QuestionStatsOut:
    return QuestionStatsOut(**{**vars(s), "options": [OptionStatOut(**vars(o)) for o in s.options]})


class FacetsOut(BaseModel):
    subjects: dict[str, int]
    types: dict[str, int]
    difficulties: dict[str, int]
    grades: dict[str, int]
    periods: dict[str, int]
    school_years: dict[str, int]
    tags: dict[str, int]
    topics: dict[str, int]
    untagged_documents: dict[str, int] = {}  # questions with no topic per source document ("none": no document)


# ------------------------------------------------------------------ review

class SourceDocumentOut(BaseModel):
    """The document a review row is about (same fields as the documents list)."""
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


class ReviewDocumentOut(BaseModel):
    document: SourceDocumentOut
    total: int
    counts: dict[str, int]
    spot_pending: int
    progress: float
    assigned_to: uuid.UUID | None
    assigned_name: str | None


def review_document_out(v: ReviewDocumentView) -> ReviewDocumentOut:
    return ReviewDocumentOut(**{**vars(v), "document": SourceDocumentOut(**vars(v.document))})


class ReviewDocumentSearchBody(SearchBody):
    """`mine`: only the documents given to the caller."""
    mine: bool = False


class AssignIn(BaseModel):
    assigned_to: uuid.UUID | None


class AnswerKeyIn(BaseModel):
    text: str


class AnswerKeyOut(BaseModel):
    applied: int
    approved: int
    unmatched: list[int]


class ApprovedOut(BaseModel):
    approved: int


class FlaggedIdsOut(BaseModel):
    flagged: list[str]
