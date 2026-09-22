"""Who takes which exam when: the window, the attempt limit, results visibility (exam-practice US-02, A-05, A-06, A-10)."""
from datetime import datetime, timedelta

from app.modules.assessment.domain.entities import RESULTS_POLICIES, Assignment, Attempt
from app.shared.domain.errors import Conflict, Invalid

MAX_DURATION = 600
MAX_ATTEMPTS = 20


def check_window(open_at: datetime, close_at: datetime, duration_minutes: int, max_attempts: int = 1,
                 results_policy: str = "after_submit") -> None:
    if close_at <= open_at:
        raise Invalid("Thời gian đóng phải sau thời gian mở", "close_at")
    if not 1 <= duration_minutes <= MAX_DURATION:
        raise Invalid("Thời lượng từ 1 đến 600 phút", "duration_minutes")
    if not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise Invalid("Số lượt làm từ 1 đến 20", "max_attempts")
    if results_policy not in RESULTS_POLICIES:
        raise Invalid("Chính sách xem kết quả không hợp lệ", "results_policy")


def window_state(a: Assignment, now: datetime) -> str:
    return "upcoming" if now < a.open_at else "closed" if now >= a.close_at else "open"


def check_can_start(a: Assignment, now: datetime) -> None:
    state = window_state(a, now)
    if state == "upcoming":
        raise Conflict("Bài chưa mở", code="not_open")
    if state == "closed":
        raise Conflict("Bài đã đóng", code="closed")


def check_attempts_left(a: Assignment, used: int) -> None:
    if used >= a.max_attempts:
        raise Conflict("Bạn đã dùng hết lượt làm", code="no_attempts_left")


def attempts_left(a: Assignment, used: int) -> int:
    return max(0, a.max_attempts - used)


def deadline(a: Assignment, now: datetime) -> datetime:
    """The attempt's own time limit, never past the window's close."""
    return min(now + timedelta(minutes=a.duration_minutes), a.close_at)


def results_visible(a: Assignment | None, att: Attempt, now: datetime, score_only: bool = False) -> bool:
    """A student sees a submitted attempt's score; its details per the assignment's policy (practice: always)."""
    if att.status != "submitted":
        return False
    if a is None or score_only:
        return True
    if a.results_policy == "after_submit":
        return True
    if a.results_policy == "after_close":
        return now >= a.close_at
    return False
