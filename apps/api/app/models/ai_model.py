# moved to the ingestion module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.ingestion.domain.entities import CAPABILITIES, PROVIDERS, AiModel  # noqa: F401
from app.modules.ingestion.infrastructure import orm as _ingestion_orm  # noqa: F401
