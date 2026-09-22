"""User management inside one organisation (US-05, A-02, A-05, A-09)."""
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.core.errors import AppError, conflict, forbidden, not_found, validation
from app.core.passwords import temp_password
from app.core.security import hash_password
from app.deps import OrgScope
from app.models import ClassMember, OrganizationMember, User
from app.services import audit, auth
from app.services.paging import Col, ListParams, paginate

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,64}$")
USERNAME_MSG = "Tên đăng nhập 3–64 ký tự: chữ không dấu, số, dấu . _ -"
ORG_ROLES = ("org_admin", "teacher", "student")


def can_manage(scope: OrgScope, target_role: str) -> bool:
    """org_admin manages everyone in the org; teachers manage students only (A-05)."""
    if scope.role == "org_admin":
        return target_role in ORG_ROLES
    if scope.role == "teacher":
        return target_role == "student"
    return False


def base_username(full_name: str) -> str:
    ascii_ = unidecode(full_name or "").lower()
    ascii_ = re.sub(r"[^a-z0-9]", "", ascii_)
    return (ascii_ or "user")[:56]


def unique_username(db: Session, org_id, full_name: str, taken: set[str] | None = None) -> str:
    base = base_username(full_name)
    base = base if len(base) >= 3 else (base + "000")[:3]
    existing = set(
        u.lower() for u in db.scalars(select(User.username).where(User.organization_id == org_id, User.username.ilike(f"{base}%")))
    ) | (taken or set())
    if base not in existing:
        return base
    n = 2
    while f"{base}{n}" in existing:
        n += 1
    return f"{base}{n}"


def check_username(username: str) -> str:
    username = (username or "").strip().lower()
    if not USERNAME_RE.match(username):
        raise validation(USERNAME_MSG, "username")
    return username


def get_member(db: Session, scope: OrgScope, user_id) -> tuple[User, OrganizationMember]:
    """A user of the scope org and their membership there (any status)."""
    user = db.get(User, user_id)
    m = db.get(OrganizationMember, (user_id, scope.org_id)) if user is not None else None
    if user is None or m is None:
        raise not_found("Không tìm thấy người dùng")
    return user, m


def get_user(db: Session, scope: OrgScope, user_id) -> User:
    return get_member(db, scope, user_id)[0]


USER_COLS = {
    "username": Col(User.username),
    "full_name": Col(User.full_name),
    "email": Col(User.email),
    "role": Col(OrganizationMember.role, "exact"),  # role in the scope org
    "is_active": Col(User.is_active & OrganizationMember.is_active, "bool"),
    "must_change_password": Col(User.must_change_password, "bool"),
    "created_at": Col(User.created_at, "date"),
    "last_login_at": Col(User.last_login_at, "date"),
}


def list_users(db: Session, scope: OrgScope, params: ListParams, class_id=None):
    """Members of the scope org with their role and status there: rows of (User, OrganizationMember)."""
    stmt = (select(User, OrganizationMember).join(OrganizationMember, OrganizationMember.user_id == User.id)
            .where(OrganizationMember.organization_id == scope.org_id))
    if scope.role == "teacher":
        stmt = stmt.where(OrganizationMember.role == "student")
    if class_id:
        stmt = stmt.where(User.id.in_(select(ClassMember.user_id).where(ClassMember.class_id == class_id)))
    return paginate(db, stmt, params, USER_COLS, search=[User.username, User.full_name, User.email], scalars=False,
                    default_sort=[User.full_name, User.id])


def create_user(db: Session, scope: OrgScope, full_name: str, role: str, username: str | None = None,
                email: str | None = None, password: str | None = None) -> tuple[User, str | None]:
    if role not in ORG_ROLES:
        raise validation("Vai trò không hợp lệ", "role")
    if not can_manage(scope, role):
        raise forbidden()
    if not (full_name or "").strip():
        raise validation("Họ tên không được để trống", "full_name")
    username = check_username(username) if username else unique_username(db, scope.org_id, full_name)
    if db.scalar(select(User.id).where(User.organization_id == scope.org_id, User.username == username)):
        raise conflict("Tên đăng nhập đã tồn tại", "username")
    temp = None
    if password:
        auth.validate_new_password(password)
    else:
        temp = password = temp_password()
    user = User(organization_id=scope.org_id, username=username, full_name=full_name.strip(), email=email or None,
                role=role, password_hash=hash_password(password), must_change_password=temp is not None)
    db.add(user)
    db.flush()
    db.refresh(user)
    audit.record(db, scope.user, scope.org_id, "user.create", "user", user.id, username=username, role=role)
    return user, temp


def update_user(db: Session, scope: OrgScope, user_id, **changes) -> User:
    user, m = get_member(db, scope, user_id)
    home = user.organization_id == scope.org_id
    if not can_manage(scope, m.role):
        raise forbidden()
    if "role" in changes and changes["role"] and changes["role"] != m.role:
        if scope.role != "org_admin" or changes["role"] not in ORG_ROLES:
            raise forbidden()
        if home:
            user.role = changes["role"]  # the home membership follows (A-06)
        m.role = changes["role"]
    if not home and (changes.get("full_name") is not None or changes.get("email") is not None):
        raise AppError("forbidden", "Thông tin tài khoản do tổ chức gốc quản lý", 403)
    if changes.get("full_name") is not None:
        if not changes["full_name"].strip():
            raise validation("Họ tên không được để trống", "full_name")
        user.full_name = changes["full_name"].strip()
    if "email" in changes and changes["email"] is not None:
        user.email = changes["email"] or None
    if changes.get("is_active") is not None:
        if user.id == scope.user.id and not changes["is_active"]:
            raise AppError("forbidden", "Không thể tự khóa tài khoản của mình", 403)
        if home and changes["is_active"] != user.is_active:
            user.is_active = changes["is_active"]
            if not user.is_active:
                auth.revoke_user_tokens(db, user.id)
        m.is_active = changes["is_active"]  # outside the home org this only locks access to this org
    audit.record(db, scope.user, scope.org_id, "user.update", "user", user.id, fields=sorted(k for k, v in changes.items() if v is not None))
    return user


def reset_password(db: Session, scope: OrgScope, user_id) -> tuple[User, str]:
    user, m = get_member(db, scope, user_id)
    if not can_manage(scope, m.role):
        raise forbidden()
    if user.organization_id != scope.org_id:
        raise AppError("forbidden", "Chỉ tổ chức gốc của tài khoản đặt lại được mật khẩu", 403)
    password = temp_password()
    user.password_hash = hash_password(password)
    user.must_change_password = True
    user.failed_logins = 0
    user.locked_until = None
    auth.revoke_user_tokens(db, user.id)
    audit.record(db, scope.user, scope.org_id, "user.reset_password", "user", user.id)
    return user, password


def class_ids_by_user(db: Session, user_ids, org_id=None) -> dict:
    """Class ids per user, limited to one org's classes when `org_id` is given."""
    from app.models import SchoolClass

    stmt = select(ClassMember.class_id, ClassMember.user_id).where(ClassMember.user_id.in_(user_ids))
    if org_id is not None:
        stmt = stmt.join(SchoolClass, SchoolClass.id == ClassMember.class_id).where(SchoolClass.organization_id == org_id)
    out: dict = {}
    for cid, uid in db.execute(stmt):
        out.setdefault(uid, []).append(cid)
    return out
