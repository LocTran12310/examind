"""Bulk account import rules (AC-16, AC-17, A-08): header aliases, row checks. The file itself is read by an adapter."""
from dataclasses import dataclass, field

from app.modules.identity.domain.entities import ORG_ROLES
from app.modules.identity.domain.services.accounts import USERNAME_RE, can_manage
from app.shared.domain.errors import Invalid

MAX_ROWS = 2000
COLUMNS = {"full_name", "username", "role", "class"}
ALIASES = {"họ tên": "full_name", "ho ten": "full_name", "họ và tên": "full_name", "ten dang nhap": "username",
           "tên đăng nhập": "username", "vai trò": "role", "lớp": "class", "lop": "class"}
ROLE_ALIASES = {"hs": "student", "học sinh": "student", "gv": "teacher", "giáo viên": "teacher", "admin": "org_admin"}


@dataclass
class ImportRow:
    row: int
    full_name: str = ""
    username: str = ""
    role: str = "student"
    klass: str = ""
    errors: list[str] = field(default_factory=list)
    generated: bool = False

    def as_dict(self) -> dict:
        return {"row": self.row, "full_name": self.full_name, "username": self.username, "role": self.role,
                "class": self.klass, "errors": self.errors, "generated_username": self.generated}


def _header_key(h: str) -> str:
    h = (h or "").strip().lower().lstrip("﻿")
    return ALIASES.get(h, h)


def rows_from_table(table: list[list[str]]) -> list[dict]:
    """The sheet (first line = header) → one dict per data line with the known columns."""
    rows = [r for r in table if any((c or "").strip() for c in r)]
    if not rows:
        raise Invalid("File rỗng", "file")
    header = [_header_key(h) for h in rows[0]]
    if "full_name" not in header:
        raise Invalid("Thiếu cột full_name (họ tên)", "file")
    if len(rows) - 1 > MAX_ROWS:
        raise Invalid(f"Tối đa {MAX_ROWS} dòng mỗi lần", "file")
    return [{k: (r[i].strip() if i < len(r) and r[i] else "") for i, k in enumerate(header) if k in COLUMNS} for r in rows[1:]]


def read_rows(raw_rows: list[dict]) -> list[ImportRow]:
    rows: list[ImportRow] = []
    for i, r in enumerate(raw_rows, start=2):  # row 1 is the header
        role = (r.get("role") or "student").strip().lower()
        role = ROLE_ALIASES.get(role, role)
        rows.append(ImportRow(row=r.get("row", i), full_name=(r.get("full_name") or "").strip(),
                              username=(r.get("username") or "").strip().lower(), role=role, klass=(r.get("class") or "").strip()))
    return rows


def check_rows(rows: list[ImportRow], actor_role: str, existing: set[str]) -> set[str]:
    """Adds the errors of each row; returns the usernames the file claims (to keep generated ones apart)."""
    seen: set[str] = set()
    for r in rows:
        if not r.full_name:
            r.errors.append("Thiếu họ tên")
        if r.role not in ORG_ROLES:
            r.errors.append(f"Vai trò không hợp lệ: {r.role}")
        elif not can_manage(actor_role, r.role):
            r.errors.append("Bạn không có quyền tạo vai trò này")
        if r.username:
            if not USERNAME_RE.match(r.username):
                r.errors.append("Tên đăng nhập không hợp lệ")
            elif r.username in existing:
                r.errors.append("Tên đăng nhập đã tồn tại")
            elif r.username in seen:
                r.errors.append("Tên đăng nhập bị trùng trong file")
            seen.add(r.username)
    return seen
