from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.modules.assessment.application.dto import AssignmentView, AttemptBrief, ExamQuestionView, ExamSummary, ExamView, MyAssignmentView
from app.modules.assessment.domain.entities import Assignment, Exam
from app.shared.domain.errors import Invalid
from app.shared.interface.search_schemas import SearchBody

# ------------------------------------------------------------------ exams


class ExamSearchBody(SearchBody):
    """The subject the list is scoped to sits at the top of the body, like the bank's: an id, or "none" for the
    exams nobody gave a subject. It is a scope, not a filter — one way to narrow by subject, not two."""
    subject_id: str | None = None

    def scope(self) -> uuid.UUID | str | None:
        if self.subject_id == "none":
            return "none"
        if not self.subject_id:
            return None
        try:
            return uuid.UUID(self.subject_id)
        except ValueError:
            raise Invalid("Môn học không hợp lệ", "subject_id") from None


class ExamIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str = ""
    settings: dict | None = None


class ExamPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str | None = None
    settings: dict | None = None


class TopicRefOut(BaseModel):
    id: uuid.UUID
    name: str
    is_primary: bool
    source: str
    score: float | None


class TagRefOut(BaseModel):
    id: uuid.UUID
    group: str
    name: str


class ExamQuestionOut(BaseModel):
    """The bank's view of the question (as `POST /questions/search` returns it) plus its place in the exam."""
    id: uuid.UUID
    type: str
    stem: str
    options: list[dict]
    answer: dict | None
    solution: str
    difficulty: str | None
    grade: int | None
    status: str
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
    topics: list[TopicRefOut] = []
    tags: list[TagRefOut] = []
    page: int | None = None
    spot_check: bool = False
    duplicate_of: uuid.UUID | None = None
    source_document_id: uuid.UUID | None = None
    group: str | None = None
    flag_evidence: dict | None = None
    position: int
    section: str
    points: float
    row: int | None


class ExamOut(BaseModel):
    id: uuid.UUID
    title: str
    subject_id: uuid.UUID | None
    grade: int | None
    description: str
    settings: dict
    blueprint: list
    source: str
    question_count: int
    total_points: float
    created_at: datetime
    questions: list[ExamQuestionOut] = []


class BlueprintIn(BaseModel):
    rows: list[dict]
    seed: int | None = None
    replace: bool = True


class BlueprintOut(BaseModel):
    added: int
    shortfalls: list[dict]
    exam: ExamOut


class IdsIn(BaseModel):
    question_ids: list[uuid.UUID]


class PointsIn(BaseModel):
    points: float


def exam_question_out(v: ExamQuestionView) -> ExamQuestionOut:
    return ExamQuestionOut(**v.question, position=v.position, section=v.section, points=v.points, row=v.row)


def _exam(e: Exam, question_count: int, total_points: float, questions: list[ExamQuestionOut]) -> ExamOut:
    return ExamOut(id=e.id, title=e.title, subject_id=e.subject_id, grade=e.grade, description=e.description, settings=e.settings or {},
                   blueprint=e.blueprint or [], source=e.source, question_count=question_count, total_points=total_points,
                   created_at=e.created_at, questions=questions)


def exam_out(v: ExamView) -> ExamOut:
    return _exam(v.exam, v.question_count, v.total_points, [exam_question_out(q) for q in v.questions])


def exam_row_out(v: ExamSummary) -> ExamOut:
    """A row of the list: never with its questions."""
    return _exam(v.exam, v.question_count, v.total_points, [])


# ------------------------------------------------------------------ assignments


class AssignmentIn(BaseModel):
    exam_id: uuid.UUID
    title: str | None = Field(default=None, max_length=200)
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    results_policy: str = "after_submit"
    class_ids: list[uuid.UUID] = []
    user_ids: list[uuid.UUID] = []


class AssignmentPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    open_at: datetime | None = None
    close_at: datetime | None = None
    duration_minutes: int | None = None
    max_attempts: int | None = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    results_policy: str | None = None


class AssignmentOut(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    title: str
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    max_attempts: int
    shuffle_questions: bool
    shuffle_options: bool
    results_policy: str
    students: int = 0
    submitted: int = 0
    classes: list[str] = []


class AttemptHistoryOut(BaseModel):
    """One sitting in a student's history. `minutes` is wall-clock from start to hand-in — not the sum of the
    per-question seconds, which measures something else (class-overview-and-subjects ADR-02)."""
    attempt_id: uuid.UUID
    exam_title: str
    assignment_title: str | None
    started_at: datetime
    submitted_at: datetime | None
    minutes: int | None
    score: float | None
    max_score: float
    score10: float | None
    status: str
    auto_submitted: bool
    student_id: uuid.UUID
    student_name: str
    username: str


class AttemptBriefOut(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None
    score: float | None
    max_score: float | None
    score10: float | None = None
    needs_grading: bool


class MyAssignmentOut(BaseModel):
    assignment: AssignmentOut
    state: str
    attempts: list[AttemptBriefOut]
    attempts_left: int
    subject_id: uuid.UUID | None = None


def assignment_out(a: Assignment, students: int = 0, submitted: int = 0, classes: list[str] | None = None) -> AssignmentOut:
    return AssignmentOut(id=a.id, exam_id=a.exam_id, title=a.title, open_at=a.open_at, close_at=a.close_at, duration_minutes=a.duration_minutes,
                         max_attempts=a.max_attempts, shuffle_questions=a.shuffle_questions, shuffle_options=a.shuffle_options,
                         results_policy=a.results_policy, students=students, submitted=submitted, classes=list(classes or []))


def assignment_view_out(v: AssignmentView) -> AssignmentOut:
    return assignment_out(v.assignment, v.students, v.submitted, v.classes)


def brief_out(b: AttemptBrief) -> AttemptBriefOut:
    return AttemptBriefOut(**vars(b))


def my_assignment_out(v: MyAssignmentView) -> MyAssignmentOut:
    return MyAssignmentOut(assignment=assignment_out(v.assignment), state=v.state, attempts=[brief_out(b) for b in v.attempts],
                           attempts_left=v.attempts_left, subject_id=v.subject_id)


class StartOut(BaseModel):
    attempt_id: uuid.UUID


class TrialIn(BaseModel):
    """A trial run's answers, in the same response shapes an attempt saves: {key} · {a: bool, …} · {value} · {text}."""
    responses: dict[uuid.UUID, dict | None] = {}


# ------------------------------------------------------------------ attempts


class AnswerIn(BaseModel):
    response: dict | None
    seconds_spent: int | None = None  # the runner's measure since the last save; clamped, never refused
    first_seen_at: datetime | None = None


class GradeIn(BaseModel):
    points: float
    comment: str | None = None
