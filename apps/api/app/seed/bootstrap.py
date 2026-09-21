"""Idempotent bootstrap: system org + super admin. Run on every api start."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import db as dbmod
from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Organization, User
from app.models.org import SYSTEM_ORG_CODE


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
    from app.core import storage

    with dbmod.session_factory()() as db:
        seed_system(db)
        extra_seeders(db)
        db.commit()
    try:
        storage.ensure_bucket()
    except Exception as exc:  # storage may come up later; health reports it
        print(f"bucket bootstrap skipped: {exc}")


def extra_seeders(db: Session) -> None:
    """Hook for later features (org templates, demo content)."""


if __name__ == "__main__":
    run()
