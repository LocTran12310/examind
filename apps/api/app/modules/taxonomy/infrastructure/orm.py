"""Maps the taxonomy dataclasses onto their tables (architecture-refactor ADR-01). Importing this module
is enough; mapping happens once."""
from app.modules.taxonomy.domain.entities import Tag
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.taxonomy import tags


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


if not _mapped(Tag):
    mapper_registry.map_imperatively(Tag, tags)
