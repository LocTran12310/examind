"""Organisation lifecycle for super admins (US-04, A-01, A-04, A-15)."""
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, conflict, not_found, validation
from app.core.passwords import temp_password
from app.core.security import hash_password, now
from app.models import Organization, User
from app.seed.org_template import seed_org
from app.services.paging import Col, ListParams, paginate
from app.services import audit, auth
from app.services.users import USERNAME_RE

CODE_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,30})[a-z0-9]$")
CODE_MSG = "Mã tổ chức 3–32 ký tự, chỉ gồm chữ không dấu, số và dấu gạch ngang"


def normalise_code(code: str) -> str:
    code = (code or "").strip().lower()
    if not CODE_RE.match(code):
        raise validation(CODE_MSG, "code")
    return code


def _get(db: Session, org_id) -> Organization:
    org = db.get(Organization, org_id)
    if org is None:
        raise not_found("Không tìm thấy tổ chức")
    return org


def _guard_system(org: Organization) -> None:
    if org.is_system:
        raise AppError("forbidden", "Không thể thay đổi tổ chức hệ thống", 403)


def user_counts(db: Session, org_ids) -> dict:
    from app.models import OrganizationMember

    rows = db.execute(select(OrganizationMember.organization_id, func.count()).where(OrganizationMember.organization_id.in_(org_ids),
                                                                                   OrganizationMember.is_active.is_(True))
                      .group_by(OrganizationMember.organization_id))
    return dict(rows.all())


ORG_COLS = {
    "code": Col(Organization.code),
    "name": Col(Organization.name),
    "status": Col(Organization.status, "exact"),
    "created_at": Col(Organization.created_at, "date"),
}


def list_orgs(db: Session, params: ListParams, include_deleted: bool = False):
    stmt = select(Organization)
    if not include_deleted:
        stmt = stmt.where(Organization.deleted_at.is_(None))
    return paginate(db, stmt, params, ORG_COLS, search=[Organization.code, Organization.name],
                    default_sort=[Organization.is_system.desc(), Organization.created_at.desc()])


def create_org(db: Session, actor: User, code: str, name: str, admin_username: str, admin_full_name: str):
    code = normalise_code(code)
    username = (admin_username or "").strip().lower()
    if not USERNAME_RE.match(username):
        raise validation("Tên đăng nhập 3–64 ký tự: chữ không dấu, số, dấu . _ -", "admin_username")
    if db.scalar(select(Organization.id).where(Organization.code == code)):
        raise conflict("Mã tổ chức đã tồn tại", "code")
    org = Organization(code=code, name=name.strip())
    db.add(org)
    db.flush()
    seed_org(db, org.id)
    password = temp_password()
    admin = User(organization_id=org.id, username=username, full_name=admin_full_name.strip(), role="org_admin",
                 password_hash=hash_password(password), must_change_password=True)
    db.add(admin)
    db.flush()
    from app.seed.bootstrap import seed_demo

    seed_demo(db, org.id)
    audit.record(db, actor, org.id, "org.create", "organization", org.id, code=code)
    return org, admin, password


def update_org(db: Session, actor: User, org_id, code: str | None, name: str | None) -> Organization:
    org = _get(db, org_id)
    if code is not None and code.strip().lower() != org.code:
        _guard_system(org)
        new = normalise_code(code)
        if db.scalar(select(Organization.id).where(Organization.code == new, Organization.id != org.id)):
            raise conflict("Mã tổ chức đã tồn tại", "code")
        audit.record(db, actor, org.id, "org.rename_code", "organization", org.id, old=org.code, new=new)
        org.code = new
    if name is not None:
        if not name.strip():
            raise validation("Tên không được để trống", "name")
        org.name = name.strip()
    audit.record(db, actor, org.id, "org.update", "organization", org.id)
    return org


def set_status(db: Session, actor: User, org_id, status: str) -> Organization:
    org = _get(db, org_id)
    _guard_system(org)
    org.status = status
    if status == "suspended":
        auth.revoke_org_tokens(db, org.id)
    audit.record(db, actor, org.id, f"org.{status}", "organization", org.id)
    return org


def delete_org(db: Session, actor: User, org_id, hard: bool = False) -> None:
    org = _get(db, org_id)
    _guard_system(org)
    if not hard:
        org.deleted_at = now()
        auth.revoke_org_tokens(db, org.id)
        audit.record(db, actor, org.id, "org.delete", "organization", org.id)
        return
    non_admins = db.scalar(select(func.count()).select_from(User).where(User.organization_id == org.id, User.role != "org_admin"))
    if non_admins:
        raise AppError("org_not_empty", "Chỉ xóa vĩnh viễn được tổ chức chưa có người dùng", 409)
    from app.core.db import Base

    # delete every tenant row of this org, children first
    for table in reversed(Base.metadata.sorted_tables):
        if "organization_id" in table.c and table.name != "audit_logs":
            if table.name == "users":
                from app.models import RefreshToken

                db.execute(RefreshToken.__table__.delete().where(RefreshToken.user_id.in_(select(User.id).where(User.organization_id == org.id))))
            db.execute(table.delete().where(table.c.organization_id == org.id))
    db.execute(Base.metadata.tables["audit_logs"].delete().where(Base.metadata.tables["audit_logs"].c.organization_id == org.id))
    db.delete(org)
