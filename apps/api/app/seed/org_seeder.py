"""OrgSeeder of the identity context over this package: per-org reference data and the demo question.
Wired by the composition root (app.main)."""
import uuid

from sqlalchemy.orm import Session


class SeedOrgSeeder:
    def __init__(self, session: Session):
        self.session = session

    def seed_reference(self, org_id: uuid.UUID) -> None:
        from app.seed.org_template import seed_org

        seed_org(self.session, org_id)

    def seed_demo(self, org_id: uuid.UUID) -> None:
        from app.seed.bootstrap import seed_demo

        seed_demo(self.session, org_id)
