from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_level, require_admin
from app.modules.academic.domain.ports import LevelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteLevel:
    level_id: uuid.UUID


class DeleteLevelHandler:
    def __init__(self, levels: LevelRepository, audit: AuditTrail, uow: UnitOfWork):
        self.levels, self.audit, self.uow = levels, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteLevel) -> None:
        require_admin(actor)
        lv = load_level(self.levels, actor.org_id, cmd.level_id)
        n = self.levels.grade_count(lv.id)
        if n:
            raise Conflict(f"Cấp học còn {n} khối", code="in_use")
        self.levels.remove(lv)
        self.audit.record(actor, actor.org_id, "level.delete", "school_level", lv.id, code=lv.code)
        self.uow.commit()
