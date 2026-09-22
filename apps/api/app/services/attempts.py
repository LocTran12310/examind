"""Attempts moved to app.modules.assessment (architecture-refactor UOW-06); the sweep the old callers use."""
from sqlalchemy.orm import Session

from app.modules.assessment.interface.deps import assessment_api


def sweep_expired(db: Session) -> int:
    """Close abandoned attempts past their deadline; the caller commits."""
    return assessment_api(db).sweep_expired()
