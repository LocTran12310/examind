"""The identity columns other contexts read (lightweight `table()`s, outside the MetaData: the old layout's
declarative User / Organization / OrganizationMember still own these tables until identity moves)."""
from sqlalchemy import Boolean, DateTime, column, table
from sqlalchemy.dialects.postgresql import UUID

users = table(
    "users", column("id", UUID(as_uuid=True)), column("organization_id", UUID(as_uuid=True)), column("username"), column("full_name"),
    column("email"), column("role"), column("is_active", Boolean), column("must_change_password", Boolean),
    column("last_login_at", DateTime(timezone=True)), column("created_at", DateTime(timezone=True)),
)
organizations = table("organizations", column("id", UUID(as_uuid=True)), column("code"))
organization_members = table(
    "organization_members", column("user_id", UUID(as_uuid=True)), column("organization_id", UUID(as_uuid=True)), column("role"),
    column("is_active", Boolean),
)
