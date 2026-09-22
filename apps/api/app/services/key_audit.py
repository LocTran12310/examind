# moved to the bank module (architecture-refactor UOW-04); the worker and the tests call these names
from sqlalchemy.orm import Session

from app.modules.bank.domain.services.key_audit import FLAG, MIN_ANSWERS, RECHECK_AFTER, evidence_for  # noqa: F401
from app.modules.bank.interface.deps import bank_api


def audit(db: Session, org_id=None) -> list:
    return bank_api(db).audit_keys(org_id)
