from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_year, require_admin
from app.modules.academic.application.ports import ClassReader
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, MemberDirectory, SchoolYearRepository
from app.modules.academic.domain.services.rollover import is_graduating, next_code, next_name
from app.shared.application.actor import Actor
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class PreviewRollover:
    source_year_id: uuid.UUID
    target_code: str | None = None


class PreviewRolloverHandler:
    """Proposed class mapping (10A1 → 11A1, top grade → tốt nghiệp) with a default action per student."""

    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, reader: ClassReader,
                 directory: MemberDirectory):
        self.years, self.classes, self.grades, self.reader, self.directory = years, classes, grades, reader, directory

    def __call__(self, actor: Actor, query: PreviewRollover) -> dict:
        require_admin(actor)
        src = load_year(self.years, actor.org_id, query.source_year_id)
        target_code = query.target_code or next_code(src.code)
        if target_code <= src.code:
            raise Invalid("Năm học mới phải sau năm hiện tại", "target_code")
        top = self.grades.top_level(actor.org_id) or 12
        target = self.years.by_code(actor.org_id, target_code)
        existing = self.classes.names_in_year(target.id) if target else set()
        out = []
        for c in self.classes.of_year(src.id):
            rows = self.reader.roster(c.id)
            roles = self.directory.roles(actor.org_id, [r.user_id for r in rows])
            graduating = is_graduating(c.grade, top)
            tname, tgrade = (None, None) if graduating else next_name(c.name, c.grade)
            out.append({
                "source_class_id": c.id, "source_name": c.name, "grade": c.grade, "graduating": graduating,
                "target_name": tname, "target_grade": tgrade, "target_exists": bool(tname and tname in existing),
                "students": [{"user_id": r.user_id, "full_name": r.full_name, "username": r.username, "current_status": r.status,
                              "action": "graduate" if graduating else "promote"}
                             for r in rows if roles.get(r.user_id) == "student"],
            })
        return {"source_year": {"id": src.id, "code": src.code, "status": src.status}, "target_code": target_code,
                "target_year_id": target.id if target else None, "top_grade": top, "classes": out}
