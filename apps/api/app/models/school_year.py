# moved to the academic module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.academic.domain.entities import TERMS, YEAR_STATUSES, SchoolTerm, SchoolYear  # noqa: F401
from app.modules.academic.infrastructure import orm as _academic_orm  # noqa: F401
