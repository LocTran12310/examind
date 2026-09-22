from app.modules.identity.application.common import load_org, load_user
from app.modules.identity.application.dto import MeView, me_view
from app.modules.identity.domain.ports import OrganizationRepository, UserRepository
from app.shared.application.actor import Actor


class GetMeHandler:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository):
        self.users, self.orgs = users, orgs

    def __call__(self, actor: Actor) -> MeView:
        user = load_user(self.users, actor.user_id)
        return me_view(user, load_org(self.orgs, user.organization_id), self.orgs.get(actor.org_id), actor.role)
