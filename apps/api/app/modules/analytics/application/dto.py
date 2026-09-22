from dataclasses import dataclass
from datetime import datetime
import uuid

from app.modules.analytics.domain.services.reports import check_reader
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class ReportFilters:
    """What a report is narrowed to (every field optional). `class_id` is the class the student was in when answering,
    not the current one (school-years ADR-02)."""
    class_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None
    assignment_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    school_year_id: uuid.UUID | None = None
    term_code: str | None = None


@dataclass(frozen=True)
class FactScope:
    """The answer facts a report reads: the org's, narrowed by the filters; a student only ever sees their own."""
    org_id: uuid.UUID
    filters: ReportFilters

    @classmethod
    def of(cls, actor: Actor, filters: ReportFilters) -> "FactScope":
        if actor.role == "student":
            filters = ReportFilters(**{**vars(filters), "student_id": actor.user_id})
        else:
            check_reader(actor.role)
        return cls(actor.org_id, filters)
