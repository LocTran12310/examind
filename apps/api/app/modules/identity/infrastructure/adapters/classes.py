"""ClassDirectory over the academic context's application API. The API object is handed in by the composition root:
identity never imports another module."""
from typing import Protocol
import uuid

from app.shared.application.actor import Actor


class _AcademicClasses(Protocol):
    def find_or_create_class(self, actor: Actor, name: str, school_year: str | None = None, grade: int | None = None): ...

    def add_members(self, actor: Actor, class_id: uuid.UUID, user_ids: set[uuid.UUID]) -> None: ...

    def leave_org_classes(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None: ...


class AcademicClassDirectory:
    def __init__(self, academic: _AcademicClasses):
        self.academic = academic

    def find_or_create(self, actor: Actor, name: str) -> uuid.UUID:
        return self.academic.find_or_create_class(actor, name).id

    def enroll(self, actor: Actor, class_id: uuid.UUID, user_ids: set[uuid.UUID]) -> None:
        self.academic.add_members(actor, class_id, user_ids)

    def leave_org_classes(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.academic.leave_org_classes(org_id, user_id)
