"""Chuyển năm học rules (school-years ADR-03, A-07): 10A1 → 11A1, the top grade graduates."""
import re

# student action → enrollment status left in the source class
ACTIONS = {"promote": "promoted", "retain": "retained", "transfer": "transferred", "graduate": "graduated"}
LEADING = re.compile(r"^(\d{1,2})(.*)$")


def next_code(code: str) -> str:
    a = int(code[5:])
    return f"{a}-{a + 1}"


def next_name(name: str, grade: int | None) -> tuple[str, int | None]:
    """10A1 → (11A1, 11); a name without a leading number keeps its name and moves up a grade."""
    m = LEADING.match(name.strip())
    if m:
        n = int(m.group(1)) + 1
        return f"{n}{m.group(2)}", n
    return name.strip(), (grade + 1) if grade else None


def is_graduating(grade: int | None, top_grade: int) -> bool:
    return grade is not None and grade >= top_grade
