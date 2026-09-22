from dataclasses import dataclass
import uuid

from app.modules.academic.application.commands._structure import check_level
from app.modules.academic.application.common import load_level, require_admin
from app.modules.academic.application.dto import LevelView, level_view
from app.modules.academic.domain.ports import LevelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class UpdateLevel:
    level_id: uuid.UUID
    code: str | None = None
    name: str | None = None
    grade_from: int | None = None
    grade_to: int | None = None
    sort: int | None = None


class UpdateLevelHandler:
    """A new range must still hold every grade of the level."""

    def __init__(self, levels: LevelRepository, audit: AuditTrail, uow: UnitOfWork):
        self.levels, self.audit, self.uow = levels, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateLevel) -> LevelView:
        require_admin(actor)
        lv = load_level(self.levels, actor.org_id, cmd.level_id)
        lo = cmd.grade_from if cmd.grade_from is not None else lv.grade_from
        hi = cmd.grade_to if cmd.grade_to is not None else lv.grade_to
        code = check_level(self.levels, actor.org_id, cmd.code or lv.code, lo, hi, lv.id)
        outside = self.levels.grades_outside(lv.id, lo, hi)
        if outside:
            raise Invalid(f"Còn {outside} khối nằm ngoài khoảng mới", "grade_from")
        lv.code, lv.grade_from, lv.grade_to = code, lo, hi
        if cmd.name:
            lv.name = cmd.name.strip()
        if cmd.sort is not None:
            lv.sort = cmd.sort
        self.audit.record(actor, actor.org_id, "level.update", "school_level", lv.id)
        self.uow.commit()
        return level_view(lv)
