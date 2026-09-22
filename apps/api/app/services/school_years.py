"""Moved to app.modules.academic (architecture-refactor); the old layout's callers (answer facts, seeds) use these."""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.modules.academic.domain.services.calendar import default_dates  # noqa: F401
from app.modules.academic.interface.deps import academic_api


def current_code(today: date | None = None) -> str:
    return academic_api(None).current_code(today)


def active_year(db: Session, org_id):
    return academic_api(db).active_year(org_id)


def year_for_date(db: Session, org_id, when: date | datetime):
    return academic_api(db).year_for_date(org_id, when)


def term_for_date(year, when: date | datetime) -> str | None:
    return academic_api(None).term_for_date(year, when)


def ensure_year(db: Session, org_id, code: str, actor=None):
    """`actor`: a User of the old layout — the creation is then in the history."""
    from app.shared.application.actor import Actor

    who = Actor(user_id=actor.id, org_id=org_id, role=actor.role) if actor is not None else None
    return academic_api(db).ensure_year(org_id, code, who)
