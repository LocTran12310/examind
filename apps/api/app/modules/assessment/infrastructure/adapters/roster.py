"""Roster over the academic context's (classes) and the identity context's (memberships) application APIs, handed in
by the composition root: assessment never imports another module."""
from datetime import date, datetime
from typing import Any, Protocol
import uuid

from app.modules.assessment.domain.value_objects import Snapshot


class _AcademicApi(Protocol):
    def class_names(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]: ...

    def members_of(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> set[uuid.UUID]: ...

    def classes_of(self, org_id: uuid.UUID, user_id: uuid.UUID, year_id: uuid.UUID | None = None) -> list[uuid.UUID]: ...

    def active_year(self, org_id: uuid.UUID) -> Any: ...

    def year_for_date(self, org_id: uuid.UUID, when: date | datetime) -> Any: ...

    def term_for_date(self, year: Any, when: date | datetime) -> str | None: ...


class _IdentityApi(Protocol):
    def member_ids(self, org_id: uuid.UUID, user_ids, role: str | tuple[str, ...] | None = None) -> set[uuid.UUID]: ...

    def active_member_ids(self, org_id: uuid.UUID, user_ids, role: str | tuple[str, ...] | None = None) -> set[uuid.UUID]: ...


class AcademicRoster:
    def __init__(self, academic: _AcademicApi, identity: _IdentityApi):
        self.academic, self.identity = academic, identity

    def class_names(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        return self.academic.class_names(org_id, list(class_ids)) if class_ids else {}

    def class_members(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        return self.academic.members_of(org_id, list(class_ids)) if class_ids else set()

    def classes_of(self, org_id: uuid.UUID, user_id: uuid.UUID) -> list[uuid.UUID]:
        return self.academic.classes_of(org_id, user_id)

    def students(self, org_id: uuid.UUID, user_ids: set[uuid.UUID], active_accounts: bool = False) -> set[uuid.UUID]:
        if not user_ids:
            return set()
        if active_accounts:
            return self.identity.active_member_ids(org_id, set(user_ids), "student")
        return self.identity.member_ids(org_id, set(user_ids), "student")

    def snapshot(self, org_id: uuid.UUID, student_id: uuid.UUID, when: datetime) -> Snapshot:
        y = self.academic.year_for_date(org_id, when) or self.academic.active_year(org_id)
        if y is None:
            return Snapshot()
        return Snapshot(y.id, self.academic.term_for_date(y, when), tuple(self.academic.classes_of(org_id, student_id, y.id)))
