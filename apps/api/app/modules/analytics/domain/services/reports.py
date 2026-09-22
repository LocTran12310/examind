"""Report rules over the graded answer facts (exam-practice US-05, US-06, A-09, A-10)."""
from app.shared.domain.errors import Forbidden, Invalid

GROUP_BY = ("type", "difficulty", "tag")
TERMS = ("hk1", "hk2")
STAFF = ("org_admin", "teacher")
UNCLASSIFIED = "Chưa phân loại"


def ratio(points: float, max_points: float) -> float | None:
    return round(points / max_points, 4) if max_points else None


def term(code: str | None) -> str | None:
    """Only a known term narrows a report."""
    return code if code in TERMS else None


def check_group(by: str) -> None:
    if by not in GROUP_BY:
        raise Invalid("Nhóm không hợp lệ", "by")


def check_reader(role: str) -> None:
    """Students read their own facts; staff read the org's."""
    if role != "student" and role not in STAFF:
        raise Forbidden()


def check_staff(role: str) -> None:
    if role not in STAFF:
        raise Forbidden()


def heat_level(level: int) -> int:
    return max(1, min(4, int(level)))
