"""Moved to app.modules.academic (architecture-refactor); the old layout's callers (user import, adaptive) use these."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import OrgScope
from app.models import User
from app.modules.academic.interface.deps import academic_api
from app.shared.application.actor import Actor


def _actor(scope: OrgScope) -> Actor:
    return Actor(user_id=scope.user.id, org_id=scope.org_id, role=scope.role, is_super=scope.is_super)


def find_or_create(db: Session, scope: OrgScope, name: str, school_year: str | None = None, grade: int | None = None):
    return academic_api(db).find_or_create_class(_actor(scope), name, school_year, grade)


def members(db: Session, scope: OrgScope, class_id) -> list[User]:
    ids = academic_api(db).member_ids(_actor(scope), class_id)
    by_id = {u.id: u for u in db.scalars(select(User).where(User.id.in_(ids)))} if ids else {}
    return [by_id[i] for i in ids]
