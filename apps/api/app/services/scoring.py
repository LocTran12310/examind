# moved to the assessment module (architecture-refactor UOW-06); re-exported for the old layout
from app.modules.assessment.domain.services.scoring import TF_PARTIAL, Grade, grade, same_short_answer, scaled  # noqa: F401
from app.shared.domain.answers import _num  # noqa: F401
