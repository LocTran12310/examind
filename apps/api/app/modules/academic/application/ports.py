"""Read ports of the academic context (lists, trees, reports)."""
from typing import Protocol
import uuid

from app.modules.academic.application.dto import ClassView, GradeView, LevelView, MemberView, RosterEntry, YearView
from app.shared.application.search import Page, SearchRequest


class YearReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[YearView]:
        """Filters: code, name (text) · status (enum) · start_date (day); sort also by class_count."""
        ...


class ClassReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, school_year_id: uuid.UUID | None = None,
               grade_id: uuid.UUID | None = None) -> Page[ClassView]: ...

    def members(self, class_id: uuid.UUID) -> list[MemberView]: ...

    def roster(self, class_id: uuid.UUID) -> list[RosterEntry]:
        """Every member with the enrollment status, by full name."""
        ...


class LevelReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[LevelView]: ...


class GradeReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, school_level_id: uuid.UUID | None = None) -> Page[GradeView]: ...


class StructureReader(Protocol):
    def tree(self, org_id: uuid.UUID, school_year: str | None = None, school_year_id: uuid.UUID | None = None) -> dict:
        """{levels: [{…, grades: [{…, classes: […]}]}], unassigned: [classes without a grade]} with class/student counts."""
        ...


class RecordReader(Protocol):
    def record(self, org_id: uuid.UUID, student_id: uuid.UUID) -> dict:
        """Hồ sơ học sinh: {student, years: [{year, classes, answered, ratio, attempts, terms, topics}]}, newest year first."""
        ...
