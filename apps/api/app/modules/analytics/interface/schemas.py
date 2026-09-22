"""Bodies and query parameters of the analytics endpoints. Reports answer plain JSON built by the handlers (the same
keys as before the refactor)."""
from datetime import datetime
import uuid

from pydantic import BaseModel

from app.modules.analytics.application.dto import ReportFilters
from app.modules.analytics.domain.services.reports import term


class PracticeIn(BaseModel):
    count: int = 20
    subject_id: uuid.UUID | None = None


class ClassAdaptiveIn(BaseModel):
    count: int = 15
    open_at: datetime
    close_at: datetime
    duration_minutes: int = 30
    title: str | None = None


def _day(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v) if v else None


def report_filters(class_id: uuid.UUID | None = None, student_id: uuid.UUID | None = None, assignment_id: uuid.UUID | None = None,
                   date_from: str | None = None, date_to: str | None = None, school_year_id: uuid.UUID | None = None,
                   term_code: str | None = None) -> ReportFilters:
    """FastAPI dependency: the query parameters every report accepts (an unknown term is ignored)."""
    return ReportFilters(class_id=class_id, student_id=student_id, assignment_id=assignment_id, date_from=_day(date_from),
                         date_to=_day(date_to), school_year_id=school_year_id, term_code=term(term_code))
