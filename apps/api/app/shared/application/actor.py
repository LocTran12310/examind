from dataclasses import dataclass
import uuid

STAFF_ROLES = ("org_admin", "teacher")


@dataclass(frozen=True)
class Actor:
    """Who is calling, in which organisation, with which role there."""
    user_id: uuid.UUID
    org_id: uuid.UUID
    role: str
    is_super: bool = False

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF_ROLES
