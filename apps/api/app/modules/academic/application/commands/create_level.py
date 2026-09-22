from dataclasses import dataclass

from app.modules.academic.application.commands._structure import check_level
from app.modules.academic.application.common import require_admin
from app.modules.academic.application.dto import LevelView, level_view
from app.modules.academic.domain.entities import SchoolLevel
from app.modules.academic.domain.ports import LevelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateLevel:
    code: str
    name: str
    grade_from: int
    grade_to: int
    sort: int = 0


class CreateLevelHandler:
    def __init__(self, levels: LevelRepository, audit: AuditTrail, uow: UnitOfWork):
        self.levels, self.audit, self.uow = levels, audit, uow

    def __call__(self, actor: Actor, cmd: CreateLevel) -> LevelView:
        require_admin(actor)
        code = check_level(self.levels, actor.org_id, cmd.code, cmd.grade_from, cmd.grade_to)
        lv = SchoolLevel(organization_id=actor.org_id, code=code, name=cmd.name.strip(), grade_from=cmd.grade_from,
                         grade_to=cmd.grade_to, sort=cmd.sort)
        self.levels.add(lv)
        self.audit.record(actor, actor.org_id, "level.create", "school_level", lv.id, code=code)
        self.uow.commit()
        return level_view(lv)
