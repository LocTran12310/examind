from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, event, func, inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, IdMixin, TimestampMixin
from app.models.org import Organization

ROLES = ("super_admin", "org_admin", "teacher", "student")


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "username", name="uq_users_org_username"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    username: Mapped[str] = mapped_column(CITEXT)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    first_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # organization_id is the home org (login namespace); last_org_id the org opened last (ADR-02, A-07)
    last_org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"))

    organization: Mapped[Organization] = relationship(lazy="joined", foreign_keys=[organization_id])


class OrganizationMember(Base):
    """A user's rights in one organisation; the home org always has a row (school-structure-multi-org ADR-02)."""
    __tablename__ = "organization_members"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


@event.listens_for(User, "after_insert")
def _home_membership(mapper, connection, user: User) -> None:
    """Every account gets its home membership, whichever code path created it."""
    connection.execute(
        pg_insert(OrganizationMember.__table__)
        .values(user_id=user.id, organization_id=user.organization_id, role=user.role, is_active=True)
        .on_conflict_do_nothing()
    )


@event.listens_for(User, "after_update")
def _sync_home_role(mapper, connection, user: User) -> None:
    """users.role mirrors the home membership (A-06)."""
    if inspect(user).attrs.role.history.has_changes():
        connection.execute(
            OrganizationMember.__table__.update()
            .where(OrganizationMember.user_id == user.id, OrganizationMember.organization_id == user.organization_id)
            .values(role=user.role)
        )


class RefreshToken(IdMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
