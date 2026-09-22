from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.ai_access import editable, load_visible, may_see_models
from app.modules.ingestion.domain.ports import AiModelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class DeleteAiModel:
    model_id: uuid.UUID


class DeleteAiModelHandler:
    def __init__(self, models: AiModelRepository, audit: AuditTrail, uow: UnitOfWork):
        self.models, self.audit, self.uow = models, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteAiModel) -> None:
        may_see_models(actor)
        m = load_visible(self.models, actor, cmd.model_id)
        if not editable(actor, m):
            raise Forbidden()
        self.models.remove(m)
        self.audit.record(actor, actor.org_id, "ai_model.delete", "ai_model", m.id)
        self.uow.commit()
