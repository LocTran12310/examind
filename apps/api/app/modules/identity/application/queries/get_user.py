from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import home_code, load_member
from app.modules.identity.application.dto import UserView, user_view
from app.modules.identity.application.ports import UserReader
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.modules.identity.domain.services.accounts import can_manage
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class GetUser:
    user_id: uuid.UUID


class GetUserHandler:
    def __init__(self, users: UserRepository, members: MembershipRepository, orgs: OrganizationRepository, reader: UserReader):
        self.users, self.members, self.orgs, self.reader = users, members, orgs, reader

    def __call__(self, actor: Actor, query: GetUser) -> UserView:
        user, m = load_member(self.users, self.members, actor.org_id, query.user_id)
        if not can_manage(actor.role, m.role) and actor.role != "org_admin":
            raise Forbidden()
        return user_view(user, home_code(self.orgs, user), m, self.reader.class_ids(actor.org_id, [user.id]).get(user.id))
