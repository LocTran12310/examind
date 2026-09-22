"""Maps the taxonomy dataclasses onto their tables (architecture-refactor ADR-01). Importing this module
is enough; mapping happens once."""
from app.modules.taxonomy.domain.entities import Semester, Subject, Tag
from app.modules.taxonomy.domain.topics import Topic
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.taxonomy import semesters, subjects, tags, topics


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


for _cls, _table in ((Tag, tags), (Subject, subjects), (Semester, semesters), (Topic, topics)):
    if not _mapped(_cls):
        mapper_registry.map_imperatively(_cls, _table)
