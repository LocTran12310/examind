from datetime import date, datetime

from app.core.timezone import business_date, business_today


class TzCalendar:
    """BusinessCalendar in `settings.business_tz`."""

    def today(self) -> date:
        return business_today()

    def day_of(self, when: date | datetime) -> date:
        return business_date(when)
