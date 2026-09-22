from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import audit_class, load_class
from app.modules.academic.domain.ports import ClassRepository, MemberDirectory, SchoolYearRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class AddMembers:
    class_id: uuid.UUID
    user_ids: list[uuid.UUID]


class AddMembersHandler:
    """Accounts of the org only; adding someone already in the class changes nothing. A student may be in several classes."""

    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, directory: MemberDirectory, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.classes, self.directory, self.audit, self.uow = years, classes, directory, audit, uow

    def __call__(self, actor: Actor, cmd: AddMembers) -> int:
        c = load_class(self.classes, actor.org_id, cmd.class_id)
        ids = set(cmd.user_ids)
        valid = self.directory.member_ids(actor.org_id, ids)
        if ids - valid:
            raise NotFound("Không tìm thấy người dùng")
        if valid:
            self.classes.add_members(c.id, valid)
            audit_class(self.audit, self.years, actor, "class.members_add", c, user_ids=[str(u) for u in valid])
        self.uow.commit()
        return len(valid)
