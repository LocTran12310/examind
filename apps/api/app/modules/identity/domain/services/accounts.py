"""Account rules: who manages whom, usernames, passwords, organisation codes (US-05, A-02, A-05, A-09)."""
import re

from unidecode import unidecode

from app.modules.identity.domain.entities import ORG_ROLES
from app.shared.domain.errors import Invalid

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,64}$")
USERNAME_MSG = "Tên đăng nhập 3–64 ký tự: chữ không dấu, số, dấu . _ -"
ORG_CODE_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,30})[a-z0-9]$")
ORG_CODE_MSG = "Mã tổ chức 3–32 ký tự, chỉ gồm chữ không dấu, số và dấu gạch ngang"
MIN_PASSWORD = 8


def can_manage(actor_role: str, target_role: str) -> bool:
    """org_admin manages everyone in the org; teachers manage students only (A-05)."""
    if actor_role == "org_admin":
        return target_role in ORG_ROLES
    if actor_role == "teacher":
        return target_role == "student"
    return False


def base_username(full_name: str) -> str:
    ascii_ = unidecode(full_name or "").lower()
    ascii_ = re.sub(r"[^a-z0-9]", "", ascii_)
    return (ascii_ or "user")[:56]


def username_base(full_name: str) -> str:
    """The stem a generated username grows from (at least 3 characters)."""
    base = base_username(full_name)
    return base if len(base) >= 3 else (base + "000")[:3]


def next_free_username(base: str, taken: set[str]) -> str:
    """`base`, else `base2`, `base3`… — `taken` holds lower-cased usernames."""
    if base not in taken:
        return base
    n = 2
    while f"{base}{n}" in taken:
        n += 1
    return f"{base}{n}"


def check_username(username: str, field: str = "username") -> str:
    username = (username or "").strip().lower()
    if not USERNAME_RE.match(username):
        raise Invalid(USERNAME_MSG, field)
    return username


def check_new_password(new_password: str) -> None:
    if len(new_password or "") < MIN_PASSWORD:
        raise Invalid(f"Mật khẩu tối thiểu {MIN_PASSWORD} ký tự", "new_password")


def normalise_org_code(code: str) -> str:
    """Login form spelling: org codes are case-insensitive."""
    return (code or "").strip().lower()


def check_org_code(code: str) -> str:
    code = normalise_org_code(code)
    if not ORG_CODE_RE.match(code):
        raise Invalid(ORG_CODE_MSG, "code")
    return code


def check_role(role: str) -> None:
    if role not in ORG_ROLES:
        raise Invalid("Vai trò không hợp lệ", "role")
