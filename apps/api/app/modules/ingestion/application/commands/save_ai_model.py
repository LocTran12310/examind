from dataclasses import dataclass, field
import uuid

from app.modules.ingestion.application.ai_access import editable, is_super, load_visible, may_manage_models, may_see_models, model_view
from app.modules.ingestion.application.dto import AiModelView
from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.ports import AiModelRepository, KeyCipher
from app.modules.ingestion.domain.services.ai_models import DEFAULT_URLS, check
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class CreateAiModel:
    name: str
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    capabilities: list[str] = field(default_factory=lambda: ["text"])
    is_free: bool = True
    enabled: bool = True


class CreateAiModelHandler:
    """An org admin registers a model for the org; the platform admin one for every org. The API key is stored encrypted."""

    def __init__(self, models: AiModelRepository, cipher: KeyCipher, audit: AuditTrail, uow: UnitOfWork):
        self.models, self.cipher, self.audit, self.uow = models, cipher, audit, uow

    def __call__(self, actor: Actor, cmd: CreateAiModel) -> AiModelView:
        may_see_models(actor)
        may_manage_models(actor)
        check(cmd.provider, cmd.model, cmd.base_url, cmd.capabilities, cmd.name)
        m = AiModel(organization_id=None if is_super(actor) else actor.org_id, name=cmd.name.strip(), provider=cmd.provider,
                    model=cmd.model.strip(), base_url=(cmd.base_url or DEFAULT_URLS[cmd.provider]).rstrip("/"),
                    api_key_enc=self.cipher.encrypt(cmd.api_key) if cmd.api_key else None,
                    capabilities=cmd.capabilities, is_free=cmd.is_free, enabled=cmd.enabled)
        self.models.add(m)
        self.audit.record(actor, actor.org_id, "ai_model.create", "ai_model", m.id, provider=cmd.provider, model=m.model)
        self.uow.commit()
        return model_view(actor, m)


@dataclass(frozen=True)
class UpdateAiModel:
    model_id: uuid.UUID
    changes: dict  # name, provider, model, base_url, capabilities, is_free, enabled; api_key ("" clears it); None = unchanged


class UpdateAiModelHandler:
    def __init__(self, models: AiModelRepository, cipher: KeyCipher, audit: AuditTrail, uow: UnitOfWork):
        self.models, self.cipher, self.audit, self.uow = models, cipher, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateAiModel) -> AiModelView:
        may_see_models(actor)
        m = load_visible(self.models, actor, cmd.model_id)
        if not editable(actor, m):
            raise Forbidden()
        changes = cmd.changes
        for k in ("name", "provider", "model", "base_url", "capabilities", "is_free", "enabled"):
            if changes.get(k) is not None:
                setattr(m, k, changes[k].strip() if isinstance(changes[k], str) else changes[k])
        check(m.provider, m.model, m.base_url, m.capabilities, m.name)
        if changes.get("api_key") is not None:
            m.api_key_enc = self.cipher.encrypt(changes["api_key"]) if changes["api_key"] else None
        self.audit.record(actor, actor.org_id, "ai_model.update", "ai_model", m.id)
        self.uow.commit()
        return model_view(actor, m)
