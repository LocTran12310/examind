"""Bulk account import from CSV/XLSX (AC-16, AC-17, A-08): preview every row, then create all or nothing."""
from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import generate_username
from app.modules.identity.application.dto import ImportPreview
from app.modules.identity.application.ports import ClassDirectory, SpreadsheetReader
from app.modules.identity.domain.entities import User
from app.modules.identity.domain.ports import PasswordHasher, Secrets, UserRepository
from app.modules.identity.domain.services.user_import import ImportRow, check_rows, read_rows, rows_from_table
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


def validate_rows(users: UserRepository, actor: Actor, raw_rows: list[dict]) -> list[ImportRow]:
    rows = read_rows(raw_rows)
    given = [r.username for r in rows if r.username]
    existing = users.taken_usernames(actor.org_id, given) if given else set()
    seen = check_rows(rows, actor.role, existing)
    for r in rows:
        if not r.username and r.full_name:
            r.username = generate_username(users, actor.org_id, r.full_name, taken=seen)
            r.generated = True
            seen.add(r.username)
    return rows


@dataclass(frozen=True)
class PreviewImport:
    filename: str
    data: bytes


class PreviewImportHandler:
    def __init__(self, users: UserRepository, sheets: SpreadsheetReader):
        self.users, self.sheets = users, sheets

    def __call__(self, actor: Actor, cmd: PreviewImport) -> ImportPreview:
        raw = rows_from_table(self.sheets.table(cmd.filename or "", cmd.data))
        rows = [r.as_dict() for r in validate_rows(self.users, actor, raw)]
        errors = sum(1 for r in rows if r["errors"])
        return ImportPreview(rows=rows, valid_count=len(rows) - errors, error_count=errors)


@dataclass(frozen=True)
class CommitImport:
    rows: list[dict]


class CommitImportHandler:
    """Every account gets a temporary password to change on first login; each class named on the row enrols the account.

    A cell naming several classes is what the export writes for a student who is in more than one, so reading it back
    has to enrol into each of them — joining them into one name would quietly create a class called "12A1; 11A2"."""

    def __init__(self, users: UserRepository, classes: ClassDirectory, hasher: PasswordHasher, secrets: Secrets, audit: AuditTrail,
                 uow: UnitOfWork):
        self.users, self.classes, self.hasher, self.secrets, self.audit, self.uow = users, classes, hasher, secrets, audit, uow

    def __call__(self, actor: Actor, cmd: CommitImport) -> list[dict]:
        rows = validate_rows(self.users, actor, cmd.rows)
        bad = [r.as_dict() for r in rows if r.errors]
        if bad:
            raise Invalid(f"{len(bad)} dòng có lỗi, chưa tạo tài khoản nào", code="import_invalid", fields={"rows": bad})
        created: list[dict] = []
        class_ids: dict[str, uuid.UUID] = {}
        for r in rows:
            password = self.secrets.temp_password()
            user = User(organization_id=actor.org_id, username=r.username, full_name=r.full_name, role=r.role,
                        password_hash=self.hasher.hash(password), must_change_password=True)
            self.users.add(user)
            for name in r.classes:
                if name not in class_ids:
                    class_ids[name] = self.classes.find_or_create(actor, name)
                self.classes.enroll(actor, class_ids[name], {user.id})
            created.append({"user_id": user.id, "username": r.username, "full_name": r.full_name, "role": r.role,
                            "class": "; ".join(r.classes), "temp_password": password})
        self.audit.record(actor, actor.org_id, "user.import", "user", None, count=len(created))
        self.uow.commit()
        return created
