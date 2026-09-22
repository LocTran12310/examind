"""Maps the ingestion dataclasses onto their tables (architecture-refactor ADR-01). Importing this module is enough;
mapping happens once."""
from app.modules.ingestion.domain.entities import AiModel, Asset, SourceDocument
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.ingestion import ai_models, assets, source_documents


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


if not _mapped(SourceDocument):
    mapper_registry.map_imperatively(SourceDocument, source_documents, properties={"meta": source_documents.c["metadata"]})
for _cls, _table in ((Asset, assets), (AiModel, ai_models)):
    if not _mapped(_cls):
        mapper_registry.map_imperatively(_cls, _table)
