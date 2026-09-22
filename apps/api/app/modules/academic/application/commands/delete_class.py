from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import audit_class, load_class
from app.modules.academic.domain.ports import ClassRepository, SchoolYearRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteClass:
    class_id: uuid.UUID


class DeleteClassHandler:
    """The students keep their accounts; only the memberships go."""

    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.classes, self.audit, self.uow = years, classes, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteClass) -> None:
        c = load_class(self.classes, actor.org_id, cmd.class_id)
        audit_class(self.audit, self.years, actor, "class.delete", c)
        self.classes.remove(c)
        self.uow.commit()
