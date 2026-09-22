from dataclasses import dataclass

from app.modules.ingestion.application.common import config_for
from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.domain.ports import AiModelRepository, OrgSettings
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden, Invalid


@dataclass(frozen=True)
class SaveIngestionSettings:
    values: dict


class SaveIngestionSettingsHandler:
    """The org's processing defaults (org admin); every chosen model must be usable, the OCR one able to read images."""

    def __init__(self, settings: OrgSettings, models: AiModelRepository, audit: AuditTrail, uow: UnitOfWork):
        self.settings, self.models, self.audit, self.uow = settings, models, audit, uow

    def __call__(self, actor: Actor, cmd: SaveIngestionSettings) -> dict:
        if actor.role != "org_admin":
            raise Forbidden()
        cfg = config_for(self.settings, actor.org_id, cmd.values)
        for mid in cfg["split_models"] + ([cfg["tag_model"]] if cfg["tag_model"] else []):
            if usable_model(self.models, actor.org_id, mid) is None:
                raise Invalid("Model không tồn tại hoặc đang tắt", "split_models")
        if cfg["vision_model"]:
            vm = usable_model(self.models, actor.org_id, cfg["vision_model"])
            if vm is None or "vision" not in (vm.capabilities or []):
                raise Invalid("Model đọc ảnh phải có khả năng vision", "vision_model")
        self.settings.save_ingestion(actor.org_id, cfg)
        self.audit.record(actor, actor.org_id, "org.ingestion_settings", "organization", actor.org_id)
        self.uow.commit()
        return cfg
