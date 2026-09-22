# moved to the ingestion module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.ingestion.domain.entities import DOC_STATUSES, SourceDocument  # noqa: F401
from app.modules.ingestion.infrastructure import orm as _ingestion_orm  # noqa: F401

# question links moved to the bank module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.bank.domain.entities import QuestionTag, QuestionTopic  # noqa: E402,F401
from app.modules.bank.infrastructure import orm as _bank_orm  # noqa: E402,F401
