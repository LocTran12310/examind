"""StaffDirectory over the identity context's application API (handed in by the composition root)."""
from typing import Protocol
import uuid

STAFF_ROLES = ("teacher", "org_admin")


class _IdentityApi(Protocol):
    def role_in(self, user_id: uuid.UUID, org_id: uuid.UUID) -> str | None: ...

    def is_super(self, user_id: uuid.UUID) -> bool: ...


class IdentityStaffDirectory:
    def __init__(self, identity: _IdentityApi):
        self.identity = identity

    def is_teacher(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return self.identity.role_in(user_id, org_id) in STAFF_ROLES and not self.identity.is_super(user_id)
