from datetime import date, datetime
from typing import Protocol


class BusinessCalendar(Protocol):
    """Business days (one fixed zone, Asia/Ho_Chi_Minh): school years and terms are counted in them."""

    def today(self) -> date: ...

    def day_of(self, when: date | datetime) -> date: ...
