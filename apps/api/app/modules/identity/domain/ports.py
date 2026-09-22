from datetime import datetime
from typing import Protocol
import uuid

from app.modules.identity.domain.entities import Membership, Organization, RefreshToken, User


class OrganizationRepository(Protocol):
    def get(self, org_id: uuid.UUID) -> Organization | None: ...

    def by_code(self, code: str) -> Organization | None:
        """Case-insensitive (the column is citext)."""
        ...

    def code_taken(self, code: str, exclude_id: uuid.UUID | None = None) -> bool: ...

    def active(self) -> list[Organization]:
        """Not deleted, system org first, then by name."""
        ...

    def add(self, org: Organization) -> None: ...

    def purge(self, org: Organization) -> None:
        """Delete the org and every tenant row of it (children first); audit entries of the org go too."""
        ...


class UserRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> User | None: ...

    def by_username(self, org_id: uuid.UUID, username: str) -> User | None:
        """In the home org `org_id`, case-insensitive."""
        ...

    def taken_usernames(self, org_id: uuid.UUID, usernames: list[str]) -> set[str]:
        """Those of `usernames` already used in the org (lower-cased)."""
        ...

    def usernames_like(self, org_id: uuid.UUID, prefix: str) -> set[str]:
        """Usernames of the org starting with `prefix` (lower-cased)."""
        ...

    def non_admin_count(self, org_id: uuid.UUID) -> int:
        """Accounts whose home is the org and who are not its admins."""
        ...

    def add(self, user: User) -> None:
        """Flushed: the home membership is created with it."""
        ...


class MembershipRepository(Protocol):
    def get(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Membership | None: ...

    def of_user(self, user_id: uuid.UUID) -> list[tuple[Organization, str]]:
        """(org, role) of the user's active memberships in orgs not deleted, by org name."""
        ...

    def roles(self, org_id: uuid.UUID, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{user_id: role} of the active memberships of the org."""
        ...

    def add(self, m: Membership) -> None: ...

    def remove(self, m: Membership) -> None: ...


class RefreshTokenRepository(Protocol):
    def by_hash(self, token_hash: str) -> RefreshToken | None: ...

    def add(self, token: RefreshToken) -> None: ...

    def revoke(self, token_hash: str, at: datetime) -> None:
        """Revoke that token if it is still live."""
        ...

    def revoke_user(self, user_id: uuid.UUID, at: datetime) -> None: ...

    def revoke_org(self, org_id: uuid.UUID, at: datetime) -> None:
        """Every live token of the accounts whose home is the org."""
        ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str | None) -> bool:
        """Spends the same time whether or not there is a hash (unknown users cost as much as wrong passwords)."""
        ...


class Secrets(Protocol):
    def temp_password(self) -> str:
        """A readable one-time password (no 0/O, 1/l/I)."""
        ...

    def refresh_token(self) -> tuple[str, str]:
        """(raw token for the cookie, digest to store)."""
        ...

    def digest(self, raw: str) -> str: ...


class AccessTokens(Protocol):
    def issue(self, user_id: uuid.UUID, org_id: uuid.UUID, org_code: str, role: str) -> str: ...
