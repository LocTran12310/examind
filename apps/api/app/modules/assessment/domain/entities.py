"""Assessment context: an exam (its questions, points and sections), who takes it when (assignments), the attempts,
their answers and the graded answer facts reports read (exam-practice US-01..US-04)."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.ids import new_id

RESULTS_POLICIES = ("after_submit", "after_close", "never")
DEFAULT_POINTS = {"mcq": 0.25, "true_false": 1.0, "short_answer": 0.5, "essay": 1.0}
SECTION_OF_TYPE = {"mcq": "I", "true_false": "II", "short_answer": "III", "essay": "IV"}
SECTION_ORDER = ["I", "II", "III", "IV"]
EXAM_SOURCES = ("manual", "blueprint", "adaptive", "document")
STAFF_ROLES = ("org_admin", "teacher")


def default_settings() -> dict:
    return {"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10}


@dataclass(eq=False)
class Exam:
    organization_id: uuid.UUID
    title: str
    subject_id: uuid.UUID | None = None
    grade: int | None = None
    description: str = ""
    # points_by_type, scale_to; from a document: source_document_id, duration_minutes; adaptive: the plan
    settings: dict = field(default_factory=default_settings)
    blueprint: list = field(default_factory=list)  # the matrix rows it was drawn from
    source: str = "manual"  # manual | blueprint | adaptive | document
    created_by: uuid.UUID | None = None
    updated_at: datetime | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def scale_to(self) -> float:
        return float((self.settings or {}).get("scale_to", 10))

    def points_for(self, qtype: str) -> float:
        """The exam's points for a question type (its own setting, else the THPT default)."""
        return float((self.settings or {}).get("points_by_type", DEFAULT_POINTS).get(qtype, DEFAULT_POINTS.get(qtype, 1.0)))


@dataclass(eq=False)
class ExamQuestion:
    exam_id: uuid.UUID
    question_id: uuid.UUID
    position: int
    points: float
    section: str = "I"
    row: int | None = None  # blueprint row that drew it


@dataclass(eq=False)
class Assignment:
    organization_id: uuid.UUID
    exam_id: uuid.UUID
    title: str
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    results_policy: str = "after_submit"
    created_by: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


@dataclass(eq=False)
class AssignmentTarget:
    """A class or one student (exactly one of the two)."""
    assignment_id: uuid.UUID
    class_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)


@dataclass(eq=False)
class Attempt:
    """One student's sitting of an exam: timed by the server, questions (and MCQ options) in its own order."""
    organization_id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    deadline_at: datetime
    assignment_id: uuid.UUID | None = None  # None: a personal practice
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    status: str = "in_progress"  # in_progress | submitted
    score: float | None = None
    max_score: float | None = None
    needs_grading: bool = False
    question_order: list = field(default_factory=list)  # question ids (str)
    option_orders: dict = field(default_factory=dict)  # {question id: [original labels in shown order]}
    tab_switches: int = 0
    id: uuid.UUID = field(default_factory=new_id)


@dataclass(eq=False)
class AttemptAnswer:
    attempt_id: uuid.UUID
    question_id: uuid.UUID
    response: dict | None = None  # in the question's original labels
    is_correct: bool | None = None
    points: float | None = None  # None: an essay waiting for a teacher
    max_points: float = 0
    key_snapshot: dict | None = None  # the key used for grading (exam-practice ADR-03)
    comment: str | None = None
    graded_by: uuid.UUID | None = None
    updated_at: datetime | None = None


@dataclass(eq=False)
class AnswerFact:
    """One graded answer, denormalised for reporting (exam-practice ADR-01), with the student's school year, term and
    classes at grading time (school-years ADR-02)."""
    organization_id: uuid.UUID
    attempt_id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    question_id: uuid.UUID
    qtype: str
    points: float
    max_points: float
    correct_ratio: float  # points / max_points (0..1)
    assignment_id: uuid.UUID | None = None
    topic_path: str | None = None
    tag_ids: list = field(default_factory=list)
    difficulty: str | None = None
    school_year_id: uuid.UUID | None = None
    term_code: str | None = None
    class_ids: list = field(default_factory=list)
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None
