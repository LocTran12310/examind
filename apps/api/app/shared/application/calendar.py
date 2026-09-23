from datetime import date, datetime
from typing import Protocol


class BusinessCalendar(Protocol):
    """Business days (one fixed zone, Asia/Ho_Chi_Minh): school years, terms and weekly snapshots are counted in them."""

    def today(self) -> date: ...

    def day_of(self, when: date | datetime) -> date: ...

    def start_of(self, day: date) -> datetime:
        """00:00 of the business day, as a UTC instant."""
        ...
