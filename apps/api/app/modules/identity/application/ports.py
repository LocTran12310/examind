"""Read ports and the outside services the identity handlers use."""
from dataclasses import dataclass
from typing import Protocol
import uuid

from app.modules.identity.application.dto import AccountView, MembershipView, OrgView, UserView
from app.modules.identity.domain.entities import Organization, User
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class AuthPolicy:
    refresh_token_days: int = 30
    login_max_failures: int = 5
    login_lock_minutes: int = 15


class UserReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, class_id: uuid.UUID | None = None,
               students_only: bool = False) -> Page[UserView]:
        """Members of the org with their role and status there. Filters: username, full_name, email (text) · role (enum) ·
        is_active, must_change_password (bool) · created_at, last_login_at (date)."""
        ...

    def class_ids(self, org_id: uuid.UUID, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[uuid.UUID]]:
        """Class ids per user, limited to the org's classes."""
        ...


class OrgReader(Protocol):
    def search(self, req: SearchRequest, include_deleted: bool = False) -> Page[OrgView]:
        """Filters: code, name (text) · status (enum) · created_at (date)."""
        ...

    def user_counts(self, org_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Active memberships per org."""
        ...


class AccountReader(Protocol):
    def search(self, req: SearchRequest) -> Page[AccountView]:
        """Every account outside the system org. Filters: username, full_name, home_org_code (text) · is_active (bool)."""
        ...


class MembershipReader(Protocol):
    def of_org(self, org: Organization, req: SearchRequest) -> Page[MembershipView]:
        """Org → users. Filters: username, full_name (text) · role (enum) · is_active (bool)."""
        ...

    def of_user(self, user: User, req: SearchRequest) -> Page[MembershipView]:
        """User → orgs, home org first. Filters: org_code, org_name (text) · role (enum)."""
        ...


class ClassDirectory(Protocol):
    """Classes of the academic context, as the user import and membership removal need them."""

    def find_or_create(self, actor: Actor, name: str) -> uuid.UUID:
        """A class of the active year by name (created when missing)."""
        ...

    def enroll(self, actor: Actor, class_id: uuid.UUID, user_ids: set[uuid.UUID]) -> None: ...

    def leave_org_classes(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """The user leaves every class of the org."""
        ...


class OrgSeeder(Protocol):
    def seed_reference(self, org_id: uuid.UUID) -> None:
        """Reference data of a new org (subjects, topics, structure)."""
        ...

    def seed_demo(self, org_id: uuid.UUID) -> None:
        """Demo content (skipped quietly when storage is down)."""
        ...


class SpreadsheetReader(Protocol):
    def table(self, filename: str, data: bytes) -> list[list[str]]:
        """The cells of a .csv/.txt (UTF-8) or .xlsx file, as text."""
        ...


class LoginThrottle(Protocol):
    def hit(self, key: str) -> bool:
        """Record an attempt; False when the key is over its limit."""
        ...
