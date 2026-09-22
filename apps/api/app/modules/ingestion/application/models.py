"""Which registered AI models an org may use (worker side: no actor)."""
import uuid

from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.ports import AiModelRepository


def usable_model(models: AiModelRepository, org_id: uuid.UUID, model_id) -> AiModel | None:
    """The model if it is enabled and belongs to the org or to every org; None for a bad or foreign id."""
    try:
        m = models.get(uuid.UUID(str(model_id)))
    except (ValueError, TypeError):
        return None
    if m is None or not m.usable_by(org_id):
        return None
    return m
