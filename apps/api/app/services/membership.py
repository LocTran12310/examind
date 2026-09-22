"""Users in several organisations (school-structure-multi-org ADR-02…ADR-04).

The home org (`users.organization_id`) is where the username lives; `organization_members`
says what the user may do in each org. Super admins work in any org as org_admin (ADR-04).
"""
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, conflict, forbidden, not_found, validation
from app.models import ClassMember, OrganizationMember, Organization, SchoolClass, User
from app.models.org import SYSTEM_ORG_CODE
from app.services import audit

ORG_ROLES = ("org_admin", "teacher", "student")


def is_super(user: User) -> bool:
    return user.role == "super_admin"


def role_in(db: Session, user: User, org_id) -> str | None:
    """The user's role in `org_id`, or None when they may not work there."""
    if is_super(user):
        org = db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            return None
        return "super_admin" if org.is_system else "org_admin"
    m = db.get(OrganizationMember, (user.id, org_id))
    return m.role if m is not None and m.is_active else None


def orgs_for(db: Session, user: User) -> list[tuple[Organization, str]]:
    """Organisations the user can switch to (active ones only), home first."""
    if is_super(user):
        orgs = db.scalars(select(Organization).where(Organization.deleted_at.is_(None)).order_by(Organization.is_system.desc(), Organization.name)).all()
        return [(o, "super_admin" if o.is_system else "org_admin") for o in orgs if o.can_login]
    rows = db.execute(select(Organization, OrganizationMember.role).join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
                      .where(OrganizationMember.user_id == user.id, OrganizationMember.is_active.is_(True), Organization.deleted_at.is_(None))
                      .order_by(Organization.name)).all()
    out = [(o, r) for o, r in rows if o.can_login]
    return sorted(out, key=lambda x: x[0].id != user.organization_id)


def active_org(db: Session, user: User) -> tuple[Organization, str]:
    """The org a new session opens in: last used if still allowed, else home (A-07, A-11)."""
    for org_id in (user.last_org_id, user.organization_id):
        if org_id is None:
            continue
        org = db.get(Organization, org_id)
        role = role_in(db, user, org_id) if org is not None and org.can_login else None
        if role:
            return org, role
    raise AppError("unauthenticated", "Tổ chức của bạn đang bị khóa", 401)


def switch(db: Session, user: User, org_id) -> tuple[Organization, str]:
    org = db.get(Organization, org_id)
    role = role_in(db, user, org_id) if org is not None else None
    if org is None or role is None:
        raise forbidden()
    if not org.can_login:
        raise AppError("org_suspended", "Tổ chức đang bị khóa", 403)
    user.last_org_id = org.id
    audit.record(db, user, org.id, "org.switch", "organization", org.id)
    return org, role


def members_stmt(org_id, role: str | tuple[str, ...] | None = None):
    """Users of `org_id` (optionally with a role there) — the one place 'users of this org' is defined."""
    stmt = (select(User).join(OrganizationMember, OrganizationMember.user_id == User.id)
            .where(OrganizationMember.organization_id == org_id, OrganizationMember.is_active.is_(True)))
    if role:
        roles = (role,) if isinstance(role, str) else role
        stmt = stmt.where(OrganizationMember.role.in_(roles))
    return stmt


def member_ids(db: Session, org_id, ids, role: str | tuple[str, ...] | None = None) -> set[uuid.UUID]:
    if not ids:
        return set()
    return set(db.scalars(members_stmt(org_id, role).with_only_columns(User.id).where(User.id.in_(list(ids)))))


def link(db: Session, scope, org_code: str, username: str, role: str) -> tuple[User, OrganizationMember]:
    """Add an existing account from another org (A-10)."""
    if scope.role != "org_admin":
        raise forbidden()
    if role not in ORG_ROLES:
        raise validation("Vai trò không hợp lệ", "role")
    home = db.scalar(select(Organization).where(Organization.code == (org_code or "").strip().lower(), Organization.code != SYSTEM_ORG_CODE))
    user = db.scalar(select(User).where(User.organization_id == home.id, User.username == (username or "").strip())) if home else None
    if user is None or not user.is_active:
        raise not_found("Không tìm thấy tài khoản với mã tổ chức và tên đăng nhập này")
    existing = db.get(OrganizationMember, (user.id, scope.org_id))
    if existing is not None and existing.is_active:
        raise conflict("Tài khoản đã là thành viên của tổ chức", "username")
    if existing is None:
        existing = OrganizationMember(user_id=user.id, organization_id=scope.org_id, role=role, is_active=True)
        db.add(existing)
    else:
        existing.role, existing.is_active = role, True
    db.flush()
    audit.record(db, scope.user, scope.org_id, "member.link", "user", user.id, home=home.code, role=role)
    return user, existing


def unlink(db: Session, scope, user_id) -> None:
    if scope.role != "org_admin":
        raise forbidden()
    m = db.get(OrganizationMember, (user_id, scope.org_id))
    user = db.get(User, user_id)
    if m is None or user is None:
        raise not_found("Không tìm thấy thành viên")
    if user.organization_id == scope.org_id:
        raise validation("Không gỡ được tổ chức gốc của tài khoản", "user_id")
    db.execute(delete(ClassMember).where(ClassMember.user_id == user_id,
                                         ClassMember.class_id.in_(select(SchoolClass.id).where(SchoolClass.organization_id == scope.org_id))))
    db.delete(m)
    if user.last_org_id == scope.org_id:
        user.last_org_id = None
    audit.record(db, scope.user, scope.org_id, "member.unlink", "user", user_id)
