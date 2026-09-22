from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import load_account, load_org
from app.modules.identity.application.dto import MembershipView
from app.modules.identity.application.ports import MembershipReader
from app.modules.identity.domain.ports import OrganizationRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchOrgMembers:
    org_id: uuid.UUID
    request: SearchRequest


@dataclass(frozen=True)
class SearchUserMemberships:
    user_id: uuid.UUID
    request: SearchRequest


class SearchOrgMembersHandler:
    """Org → users (school-years AC-13)."""

    def __init__(self, orgs: OrganizationRepository, reader: MembershipReader):
        self.orgs, self.reader = orgs, reader

    def __call__(self, actor: Actor, query: SearchOrgMembers) -> Page[MembershipView]:
        return self.reader.of_org(load_org(self.orgs, query.org_id), query.request)


class SearchUserMembershipsHandler:
    """User → orgs, home org first."""

    def __init__(self, users: UserRepository, reader: MembershipReader):
        self.users, self.reader = users, reader

    def __call__(self, actor: Actor, query: SearchUserMemberships) -> Page[MembershipView]:
        return self.reader.of_user(load_account(self.users, query.user_id), query.request)
