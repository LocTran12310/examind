"""What other contexts (and the old layout) may ask the identity context (architecture-refactor ADR-01)."""
import uuid

from app.modules.identity.application.common import role_in
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository


class IdentityApi:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository):
        self.users, self.orgs, self.members = users, orgs, members

    def role_in(self, user_id: uuid.UUID, org_id: uuid.UUID) -> str | None:
        """The account's role in the org, or None when it may not work there (super admins: org_admin anywhere)."""
        user = self.users.get(user_id)
        return role_in(self.orgs, self.members, user, org_id) if user is not None else None

    def roles_in(self, org_id: uuid.UUID, user_ids) -> dict[uuid.UUID, str]:
        """{user_id: role} for the active members of the org among `user_ids`."""
        return self.members.roles(org_id, list(user_ids)) if user_ids else {}

    def member_ids(self, org_id: uuid.UUID, user_ids, role: str | tuple[str, ...] | None = None) -> set[uuid.UUID]:
        """Those of `user_ids` with an active membership in the org (optionally with one of these roles there)."""
        roles = self.roles_in(org_id, user_ids)
        wanted = None if not role else ((role,) if isinstance(role, str) else role)
        return {u for u, r in roles.items() if wanted is None or r in wanted}
