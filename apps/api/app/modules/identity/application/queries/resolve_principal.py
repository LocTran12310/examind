from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import role_in
from app.modules.identity.application.dto import Principal
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.domain.errors import Unauthenticated


@dataclass(frozen=True)
class ResolvePrincipal:
    """The claims of a valid access token."""
    user_id: uuid.UUID
    org_id: uuid.UUID | None = None


class ResolvePrincipalHandler:
    """Re-checked on every request (ADR-03): the account, its home org and its membership in the token's org must still allow it."""

    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository):
        self.users, self.orgs, self.members = users, orgs, members

    def __call__(self, query: ResolvePrincipal) -> Principal:
        user = self.users.get(query.user_id)
        home = self.orgs.get(user.organization_id) if user is not None else None
        if user is None or not user.is_active or home is None or not home.can_login:
            raise Unauthenticated()
        org_id = query.org_id or user.organization_id
        org = self.orgs.get(org_id)
        role = role_in(self.orgs, self.members, user, org_id) if org is not None and org.can_login else None
        if role is None:
            raise Unauthenticated()  # membership removed/disabled or org suspended: the client refreshes into an allowed org
        return Principal(user=user, org_id=org_id, role=role)
