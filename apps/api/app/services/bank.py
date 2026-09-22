"""The question bank moved to app.modules.bank (architecture-refactor UOW-04); what the old layout still calls."""
import uuid

from sqlalchemy.orm import Session

from app.deps import OrgScope
from app.modules.bank.application.dto import BankFilters
from app.modules.bank.infrastructure.repositories import IN_USE_CHECKS, release_duplicates_of  # noqa: F401
from app.modules.bank.interface.deps import bank_api
from app.shared.domain.errors import Invalid


def _ids(values, message: str, field: str) -> tuple[uuid.UUID, ...]:
    try:
        return tuple(dict.fromkeys(v if isinstance(v, uuid.UUID) else uuid.UUID(str(v)) for v in values if v))
    except ValueError:
        raise Invalid(message, field)


def search_ids(db: Session, scope: OrgScope, *, topic_id=None, topic_ids=None, tag_ids=None, subject_id=None, **filters) -> list:
    """Ids of the usable questions an exam blueprint row selects (same filters as the bank search)."""
    if subject_id not in (None, "none") and not isinstance(subject_id, uuid.UUID):
        subject_id = _ids([subject_id], "Môn học không hợp lệ", "subject_id")[0]
    f = BankFilters(subject_id=subject_id, topic_ids=_ids([topic_id, *(topic_ids or [])], "Chuyên đề không hợp lệ", "topic_ids"),
                    tag_ids=_ids(tag_ids or [], "Tag không hợp lệ", "tag_ids"), **filters)
    return bank_api(db).question_ids(scope.org_id, f)
