from datetime import datetime
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.identity.domain.entities import Membership, Organization, RefreshToken, User
from app.modules.identity.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.db import metadata
from app.shared.infrastructure.schema.identity import organization_members, organizations, refresh_tokens, users


class _Repo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, row) -> None:
        self.session.add(row)
        self.session.flush()

    def remove(self, row) -> None:
        self.session.delete(row)
        self.session.flush()


class SqlOrganizationRepository(_Repo):
    def get(self, org_id: uuid.UUID) -> Organization | None:
        return self.session.get(Organization, org_id)

    def by_code(self, code: str) -> Organization | None:
        return self.session.scalar(select(Organization).where(organizations.c.code == code))

    def code_taken(self, code: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(organizations.c.id).where(organizations.c.code == code)
        if exclude_id is not None:
            stmt = stmt.where(organizations.c.id != exclude_id)
        return self.session.scalar(stmt) is not None

    def active(self) -> list[Organization]:
        return list(self.session.scalars(select(Organization).where(organizations.c.deleted_at.is_(None))
                                         .order_by(organizations.c.is_system.desc(), organizations.c.name)))

    def purge(self, org: Organization) -> None:
        db = self.session
        # every tenant row of this org, children first
        for table in reversed(metadata.sorted_tables):
            if "organization_id" in table.c and table.name != "audit_logs":
                if table.name == "users":
                    db.execute(refresh_tokens.delete().where(refresh_tokens.c.user_id.in_(select(users.c.id).where(users.c.organization_id == org.id))))
                db.execute(table.delete().where(table.c.organization_id == org.id))
        audit_logs = metadata.tables["audit_logs"]
        db.execute(audit_logs.delete().where(audit_logs.c.organization_id == org.id))
        db.delete(org)
        db.flush()


class SqlUserRepository(_Repo):
    def get(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def by_username(self, org_id: uuid.UUID, username: str) -> User | None:
        return self.session.scalar(select(User).where(users.c.organization_id == org_id, users.c.username == username))

    def taken_usernames(self, org_id: uuid.UUID, usernames: list[str]) -> set[str]:
        return {u.lower() for u in self.session.scalars(select(users.c.username).where(users.c.organization_id == org_id,
                                                                                        users.c.username.in_(usernames)))}

    def usernames_like(self, org_id: uuid.UUID, prefix: str) -> set[str]:
        return {u.lower() for u in self.session.scalars(select(users.c.username).where(users.c.organization_id == org_id,
                                                                                        users.c.username.ilike(f"{prefix}%")))}

    def non_admin_count(self, org_id: uuid.UUID) -> int:
        return self.session.scalar(select(func.count()).select_from(users).where(users.c.organization_id == org_id,
                                                                                 users.c.role != "org_admin")) or 0


class SqlMembershipRepository(_Repo):
    def get(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Membership | None:
        return self.session.get(Membership, (user_id, org_id))

    def of_user(self, user_id: uuid.UUID) -> list[tuple[Organization, str]]:
        m = organization_members.c
        rows = self.session.execute(
            select(Organization, m.role).join(organization_members, m.organization_id == organizations.c.id)
            .where(m.user_id == user_id, m.is_active.is_(True), organizations.c.deleted_at.is_(None))
            .order_by(organizations.c.name)).all()
        return [(o, r) for o, r in rows]

    def roles(self, org_id: uuid.UUID, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not user_ids:
            return {}
        m = organization_members.c
        return dict(self.session.execute(select(m.user_id, m.role).where(
            m.organization_id == org_id, m.user_id.in_(list(user_ids)), m.is_active.is_(True))).all())


class SqlRefreshTokenRepository(_Repo):
    def by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.session.scalar(select(RefreshToken).where(refresh_tokens.c.token_hash == token_hash))

    def add(self, token: RefreshToken) -> None:
        self.session.add(token)

    def _revoke(self, where, at: datetime) -> None:
        # ORM-enabled update: tokens already loaded in the session see the revocation too
        self.session.execute(update(RefreshToken).where(where, refresh_tokens.c.revoked_at.is_(None)).values(revoked_at=at))

    def revoke(self, token_hash: str, at: datetime) -> None:
        self._revoke(refresh_tokens.c.token_hash == token_hash, at)

    def revoke_user(self, user_id: uuid.UUID, at: datetime) -> None:
        self._revoke(refresh_tokens.c.user_id == user_id, at)

    def revoke_org(self, org_id: uuid.UUID, at: datetime) -> None:
        self._revoke(refresh_tokens.c.user_id.in_(select(users.c.id).where(users.c.organization_id == org_id)), at)
