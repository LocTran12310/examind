"""User management inside one organisation (US-05, A-02, A-05, A-09)."""
import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.core.errors import AppError, conflict, forbidden, not_found, validation
from app.core.passwords import temp_password
from app.core.security import hash_password
from app.deps import OrgScope
from app.models import ClassMember, User
from app.services import audit, auth

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


def get_user(db: Session, scope: OrgScope, user_id) -> User:
    user = db.get(User, user_id)
    if user is None or user.organization_id != scope.org_id:
        raise not_found("Không tìm thấy người dùng")
    return user


def list_users(db: Session, scope: OrgScope, q="", role=None, class_id=None, active=None, page=1, page_size=50):
    stmt = select(User).where(User.organization_id == scope.org_id)
    if scope.role == "teacher":
        stmt = stmt.where(User.role == "student")
    if role:
        stmt = stmt.where(User.role == role)
    if active is not None:
        stmt = stmt.where(User.is_active.is_(active))
    if class_id:
        stmt = stmt.where(User.id.in_(select(ClassMember.user_id).where(ClassMember.class_id == class_id)))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.full_name.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(User.full_name).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


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
    user = get_user(db, scope, user_id)
    if not can_manage(scope, user.role):
        raise forbidden()
    if "role" in changes and changes["role"] and changes["role"] != user.role:
        if scope.role != "org_admin" or changes["role"] not in ORG_ROLES:
            raise forbidden()
        user.role = changes["role"]
    if changes.get("full_name") is not None:
        if not changes["full_name"].strip():
            raise validation("Họ tên không được để trống", "full_name")
        user.full_name = changes["full_name"].strip()
    if "email" in changes and changes["email"] is not None:
        user.email = changes["email"] or None
    if changes.get("is_active") is not None and changes["is_active"] != user.is_active:
        if user.id == scope.user.id:
            raise AppError("forbidden", "Không thể tự khóa tài khoản của mình", 403)
        user.is_active = changes["is_active"]
        if not user.is_active:
            auth.revoke_user_tokens(db, user.id)
    audit.record(db, scope.user, scope.org_id, "user.update", "user", user.id, fields=sorted(k for k, v in changes.items() if v is not None))
    return user


def reset_password(db: Session, scope: OrgScope, user_id) -> tuple[User, str]:
    user = get_user(db, scope, user_id)
    if not can_manage(scope, user.role):
        raise forbidden()
    password = temp_password()
    user.password_hash = hash_password(password)
    user.must_change_password = True
    user.failed_logins = 0
    user.locked_until = None
    auth.revoke_user_tokens(db, user.id)
    audit.record(db, scope.user, scope.org_id, "user.reset_password", "user", user.id)
    return user, password


def class_ids_by_user(db: Session, user_ids) -> dict:
    out: dict = {}
    for cid, uid in db.execute(select(ClassMember.class_id, ClassMember.user_id).where(ClassMember.user_id.in_(user_ids))):
        out.setdefault(uid, []).append(cid)
    return out
