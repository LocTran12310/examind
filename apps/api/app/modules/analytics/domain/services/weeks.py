"""The business week a mastery snapshot covers (learning-telemetry A-06): Monday to Sunday of the business calendar,
named after its Monday."""
from datetime import date, timedelta

WEEK = timedelta(days=7)


def week_start(day: date) -> date:
    """The Monday of the week `day` falls in."""
    return day - timedelta(days=day.weekday())


def every_week(first: date, last: date) -> list[date]:
    """Every week from `first` to `last` inclusive, so a series has no holes where nobody answered."""
    out, cur = [], week_start(first)
    stop = week_start(last)
    while cur <= stop:
        out.append(cur)
        cur += WEEK
    return out
