import uuid

from app.modules.academic.application.common import load_level
from app.modules.academic.domain.entities import SchoolLevel
from app.modules.academic.domain.ports import GradeRepository, LevelRepository
from app.modules.academic.domain.services.structure import check_grade_in_level, check_range, clean_level_code
from app.shared.domain.errors import Conflict, Invalid


def check_level(levels: LevelRepository, org_id: uuid.UUID, code: str, grade_from: int, grade_to: int,
                level_id: uuid.UUID | None = None) -> str:
    """A unique code and a grade range that no other level of the org covers."""
    code = clean_level_code(code)
    check_range(grade_from, grade_to)
    if levels.code_taken(org_id, code, exclude_id=level_id):
        raise Conflict("Mã cấp học đã tồn tại", "code")
    overlap = levels.overlapping(org_id, grade_from, grade_to, exclude_id=level_id)
    if overlap:
        raise Invalid(f"Khoảng khối trùng với cấp {overlap}", "grade_from")
    return code


def check_grade(levels: LevelRepository, grades: GradeRepository, org_id: uuid.UUID, level: int, school_level_id: uuid.UUID,
                grade_id: uuid.UUID | None = None) -> SchoolLevel:
    """The grade number lies in its level's range and is unique in the org."""
    lv = load_level(levels, org_id, school_level_id)
    check_grade_in_level(level, lv)
    if grades.level_taken(org_id, level, exclude_id=grade_id):
        raise Conflict(f"Khối {level} đã có", "level")
    return lv
