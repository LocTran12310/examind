"""Who sees and edits which AI models (US-04, A-10, A-11): an org sees its own and the system models; the platform
admin (in the system org) manages the system models; org admins manage their org's."""
import uuid

from app.modules.ingestion.application.dto import AiModelView
from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.ports import AiModelRepository
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden, NotFound

MODEL_ROLES = ("org_admin", "teacher", "super_admin")
MANAGER_ROLES = ("org_admin", "super_admin")


def is_super(actor: Actor) -> bool:
    return actor.role == "super_admin"


def may_see_models(actor: Actor) -> None:
    if actor.role not in MODEL_ROLES:
        raise Forbidden()


def may_manage_models(actor: Actor) -> None:
    if actor.role not in MANAGER_ROLES:
        raise Forbidden()


def editable(actor: Actor, m: AiModel) -> bool:
    if m.organization_id is None:
        return is_super(actor)
    return actor.role == "org_admin" and m.organization_id == actor.org_id


def load_visible(models: AiModelRepository, actor: Actor, model_id: uuid.UUID) -> AiModel:
    m = models.get(model_id)
    if m is None or (m.organization_id not in (None, actor.org_id)):
        raise NotFound("Không tìm thấy model")
    return m


def model_view(actor: Actor, m: AiModel) -> AiModelView:
    return AiModelView(id=m.id, name=m.name, provider=m.provider, model=m.model, base_url=m.base_url, capabilities=list(m.capabilities or []),
                       is_free=m.is_free, enabled=m.enabled, system=m.organization_id is None, has_key=bool(m.api_key_enc),
                       editable=editable(actor, m))
