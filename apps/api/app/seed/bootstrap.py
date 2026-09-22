"""Idempotent bootstrap: system org + super admin. Run on every api start."""
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.metadata  # noqa: F401  (every table and mapping)
from app.modules.identity.domain.entities import SYSTEM_ORG_CODE, Organization, User
from app.modules.identity.infrastructure.adapters.passwords import hash_password
from app.shared.infrastructure import db as dbmod
from app.shared.infrastructure.config import get_settings


def seed_system(db: Session) -> tuple[Organization, User]:
    s = get_settings()
    org = db.scalar(select(Organization).where(Organization.code == SYSTEM_ORG_CODE))
    if org is None:
        org = Organization(code=SYSTEM_ORG_CODE, name="Examind (hệ thống)", is_system=True)
        db.add(org)
        db.flush()
    admin = db.scalar(select(User).where(User.organization_id == org.id, User.username == s.superadmin_username))
    if admin is None:
        admin = User(
            organization_id=org.id,
            username=s.superadmin_username,
            password_hash=hash_password(s.superadmin_password),
            full_name="Super admin",
            role="super_admin",
            must_change_password=True,
        )
        db.add(admin)
        db.flush()
    return org, admin


def run() -> None:
    from app.shared.infrastructure import storage

    try:
        storage.ensure_bucket()
    except Exception as exc:  # storage may come up later; health reports it
        print(f"bucket bootstrap skipped: {exc}")
    with dbmod.session_factory()() as db:
        seed_system(db)
        extra_seeders(db)
        triage_legacy_drafts(db)
        backfill_mastery_if_missing(db)
        db.commit()


def extra_seeders(db: Session) -> None:
    """Backfill per-org reference data for every tenant org (idempotent)."""
    from app.seed.org_template import seed_org

    for org_id in db.scalars(select(Organization.id).where(Organization.is_system.is_(False))):
        seed_org(db, org_id)
        seed_demo(db, org_id)


def seed_demo(db: Session, org_id) -> None:
    """Demo content needs object storage; skip quietly when it is down (health reports it)."""
    from app.seed.demo_question import seed_demo_question

    try:
        with db.begin_nested():
            seed_demo_question(db, org_id)
    except Exception as exc:
        print(f"demo question skipped for {org_id}: {exc}")



def triage_legacy_drafts(db: Session) -> int:
    """Questions stored before the review workflow existed are triaged once (the bank)."""
    from app.modules.bank.interface.deps import bank_api

    return bank_api(db).triage_legacy_drafts()


def backfill_mastery_if_missing(db: Session) -> int:
    """Answers graded before mastery tracking existed (adaptive-review AC-03)."""
    from app.modules.analytics.interface.deps import analytics_api

    return analytics_api(db).rebuild_mastery_if_missing()


if __name__ == "__main__":
    run()

