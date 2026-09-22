"""School structure rules: Cấp học › Khối › Lớp (school-structure-multi-org ADR-01, A-01…A-04)."""
import re

from app.shared.domain.errors import Invalid

LEVEL_CODE_RE = re.compile(r"^[a-z0-9_-]{1,20}$")
GRADE_NUMBER = re.compile(r"^(\d{1,2})")


def clean_level_code(code: str | None) -> str:
    code = (code or "").strip().lower()
    if not LEVEL_CODE_RE.match(code):
        raise Invalid("Mã cấp học: chữ thường không dấu, số, - _", "code")
    return code


def check_range(grade_from: int, grade_to: int) -> None:
    if grade_from > grade_to:
        raise Invalid("Khối bắt đầu phải nhỏ hơn hoặc bằng khối kết thúc", "grade_to")


def check_grade_in_level(level: int, lv) -> None:
    if not lv.grade_from <= level <= lv.grade_to:
        raise Invalid(f"{lv.name} gồm khối {lv.grade_from}–{lv.grade_to}", "level")


def check_class(name: str, school_year: str, grade: int | None) -> None:
    from app.modules.academic.domain.services.calendar import is_year_code

    if not (name or "").strip():
        raise Invalid("Tên lớp không được để trống", "name")
    if not is_year_code(school_year):
        raise Invalid("Năm học dạng 2026-2027", "school_year")
    if grade is not None and not 1 <= grade <= 12:
        raise Invalid("Khối lớp từ 1 đến 12", "grade")


def grade_from_name(name: str) -> int | None:
    """"10A1" → 10 (imports that give only a class name)."""
    m = GRADE_NUMBER.match(name.strip())
    return int(m.group(1)) if m and 1 <= int(m.group(1)) <= 12 else None
