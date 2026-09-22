"""OrgSettings over organizations.settings (the `ingestion` key)."""
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.shared.infrastructure.schema.identity import organizations

o = organizations.c


class SqlOrgSettings:
    def __init__(self, session: Session):
        self.session = session

    def _settings(self, org_id: uuid.UUID) -> tuple[bool, dict]:
        self.session.flush()
        row = self.session.execute(select(o.settings).where(o.id == org_id)).first()
        return (row is not None, (row[0] or {}) if row else {})

    def ingestion(self, org_id: uuid.UUID) -> dict | None:
        found, settings = self._settings(org_id)
        return settings.get("ingestion", {}) if found else None

    def save_ingestion(self, org_id: uuid.UUID, values: dict) -> None:
        _, settings = self._settings(org_id)
        self.session.execute(update(organizations).where(o.id == org_id).values(settings={**settings, "ingestion": values})
                             .execution_options(synchronize_session=False))
        self.session.expire_all()  # a loaded Organization must see the new settings
