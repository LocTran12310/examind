from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import load_org
from app.modules.identity.application.dto import OrgView, org_view
from app.modules.identity.application.ports import OrgReader
from app.modules.identity.domain.ports import OrganizationRepository
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetOrg:
    org_id: uuid.UUID


class GetOrgHandler:
    def __init__(self, orgs: OrganizationRepository, reader: OrgReader):
        self.orgs, self.reader = orgs, reader

    def __call__(self, actor: Actor, query: GetOrg) -> OrgView:
        org = load_org(self.orgs, query.org_id)
        return org_view(org, self.reader.user_counts([org.id]).get(org.id, 0))
