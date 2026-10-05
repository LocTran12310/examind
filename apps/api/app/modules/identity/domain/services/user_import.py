"""Bulk account import rules (AC-16, AC-17, A-08): header aliases, row checks. The file itself is read by an adapter.

One vocabulary, two spellings. What the product *shows* — in the export, the template, the preview — is Vietnamese;
what it *stores* is the English key. So the header of a file is read through `ALIASES`, which holds the label of every
column beside its key, and a role cell through `ROLE_ALIASES`, which holds the label of every role beside its name.
That is what makes a file the product exported importable again without anyone translating anything: the label **is**
the key, as far as reading a file is concerned. A key-only header still works, so a file written by a script is read
the same way."""
from dataclasses import dataclass, field
import re

from app.modules.identity.domain.entities import ORG_ROLES
from app.modules.identity.domain.services.accounts import USERNAME_RE, can_manage
from app.shared.domain.errors import Invalid

MAX_ROWS = 2000
COLUMNS = {"full_name", "username", "role", "class"}
#: the label each column is written with, and the spellings a file may carry it in. The first of each is what the
#: export and the template write; the rest are what people type (no accents, another word for the same thing).
COLUMN_LABELS = {
    "full_name": ("Họ tên", "Ho ten", "Họ và tên", "Ho va ten", "Tên", "Ten"),
    "username": ("Tên đăng nhập", "Ten dang nhap", "Tài khoản", "Tai khoan"),
    "role": ("Vai trò", "Vai tro"),
    "class": ("Lớp", "Lop", "Lớp học", "Lop hoc"),
}
ALIASES = {label.lower(): key for key, labels in COLUMN_LABELS.items() for label in labels}
#: same idea for the cells of the role column. The first of each is what the export writes (`ROLE_LABEL` on the web).
ROLE_LABELS = {
    "student": ("Học sinh", "Hoc sinh", "hs"),
    "teacher": ("Giáo viên", "Giao vien", "gv"),
    "org_admin": ("Quản trị trung tâm", "Quan tri trung tam", "Quản trị", "Quan tri", "admin"),
}
ROLE_ALIASES = {label.lower(): role for role, labels in ROLE_LABELS.items() for label in labels}
#: one cell can name several classes — that is how the export writes a student who is in more than one
CLASS_SPLIT = re.compile(r"[;,]")


@dataclass
class ImportRow:
    row: int
    full_name: str = ""
    username: str = ""
    role: str = "student"
    classes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    generated: bool = False

    def as_dict(self) -> dict:
        # `class` goes back out the way it came in, so a previewed row can be sent back to be committed
        return {"row": self.row, "full_name": self.full_name, "username": self.username, "role": self.role,
                "class": "; ".join(self.classes), "errors": self.errors, "generated_username": self.generated}


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
        raise Invalid("Thiếu cột Họ tên (hoặc full_name)", "file")
    if len(rows) - 1 > MAX_ROWS:
        raise Invalid(f"Tối đa {MAX_ROWS} dòng mỗi lần", "file")
    return [{k: (r[i].strip() if i < len(r) and r[i] else "") for i, k in enumerate(header) if k in COLUMNS} for r in rows[1:]]


def read_rows(raw_rows: list[dict]) -> list[ImportRow]:
    rows: list[ImportRow] = []
    for i, r in enumerate(raw_rows, start=2):  # row 1 is the header
        role = (r.get("role") or "student").strip().lower()
        role = ROLE_ALIASES.get(role, role)
        classes = [c.strip() for c in CLASS_SPLIT.split(r.get("class") or "") if c.strip()]
        rows.append(ImportRow(row=r.get("row", i), full_name=(r.get("full_name") or "").strip(),
                              username=(r.get("username") or "").strip().lower(), role=role, classes=classes))
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
