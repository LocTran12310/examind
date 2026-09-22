from app.modules.identity.application.common import load_user, switchable_orgs
from app.modules.identity.application.dto import MyOrgView
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.application.actor import Actor


class MyOrgsHandler:
    """Organisations the header selector offers (all active ones for a super admin)."""

    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository):
        self.users, self.orgs, self.members = users, orgs, members

    def __call__(self, actor: Actor) -> list[MyOrgView]:
        user = load_user(self.users, actor.user_id)
        return [MyOrgView(o.id, o.code, o.name, role, o.id == user.organization_id) for o, role in switchable_orgs(self.orgs, self.members, user)]
