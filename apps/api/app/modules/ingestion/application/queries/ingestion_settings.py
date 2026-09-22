from app.modules.ingestion.domain.ports import OrgSettings
from app.modules.ingestion.domain.services.processing import org_defaults
from app.shared.application.actor import Actor


class GetIngestionSettingsHandler:
    """The org's processing defaults over the system default."""

    def __init__(self, settings: OrgSettings):
        self.settings = settings

    def __call__(self, actor: Actor) -> dict:
        return org_defaults(self.settings.ingestion(actor.org_id))

