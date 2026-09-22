"""Physical tables of the identity area: organisations, accounts, memberships and refresh tokens (ADR-01).
The identity module maps its dataclasses onto them; other contexts read their columns through SQLAlchemy Core."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID

from app.shared.infrastructure.db import metadata


def _id() -> Column:
    return Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created() -> Column:
    return Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


organizations = Table(
    "organizations", metadata,
    _id(),
    _created(),
    Column("code", CITEXT, unique=True, nullable=False),
    Column("name", String(200), nullable=False),
    Column("status", String(20), nullable=False, default="active"),  # active | suspended
    Column("is_system", Boolean, nullable=False, default=False),
    Column("settings", JSONB, nullable=False, default=dict),
    Column("deleted_at", DateTime(timezone=True)),
)

users = Table(
    "users", metadata,
    _id(),
    _created(),
    # the home org (login namespace); last_org_id is the org opened last (school-structure-multi-org ADR-02, A-07)
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("username", CITEXT, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("full_name", String(200), nullable=False),
    Column("email", String(255)),
    Column("role", String(20), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("must_change_password", Boolean, nullable=False, default=False),
    Column("failed_logins", Integer, nullable=False, default=0),
    Column("first_failed_at", DateTime(timezone=True)),
    Column("locked_until", DateTime(timezone=True)),
    Column("last_login_at", DateTime(timezone=True)),
    Column("last_org_id", UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")),
    UniqueConstraint("organization_id", "username", name="uq_users_org_username"),
)

# a user's rights in one organisation; the home org always has a row (school-structure-multi-org ADR-02)
organization_members = Table(
    "organization_members", metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("role", String(20), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

refresh_tokens = Table(
    "refresh_tokens", metadata,
    _id(),
    _created(),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("token_hash", String(64), unique=True, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True)),
)
