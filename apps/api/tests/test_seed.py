from sqlalchemy import func, select

from app.models import Organization, User
from app.seed.bootstrap import seed_system


def test_seed_is_idempotent(db):
    seed_system(db)
    seed_system(db)
    db.commit()
    assert db.scalar(select(func.count()).select_from(Organization).where(Organization.code == "SYSTEM")) == 1
    admins = db.scalars(select(User).where(User.role == "super_admin")).all()
    assert len(admins) == 1
    assert admins[0].must_change_password is True
    assert admins[0].password_hash.startswith("$argon2id$")
