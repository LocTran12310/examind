"""Maps the academic dataclasses onto their tables (architecture-refactor ADR-01). Importing this module
is enough; mapping happens once."""
from sqlalchemy.orm import relationship

from app.modules.academic.domain.entities import ClassMember, Grade, SchoolClass, SchoolLevel, SchoolTerm, SchoolYear
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.academic import class_members, classes, school_terms, school_years
from app.shared.infrastructure.schema.taxonomy import grades, school_levels


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


if not _mapped(SchoolYear):
    mapper_registry.map_imperatively(SchoolTerm, school_terms)
    mapper_registry.map_imperatively(SchoolYear, school_years, properties={
        "terms": relationship(SchoolTerm, order_by=school_terms.c.code, cascade="all, delete-orphan", lazy="selectin"),
    })
    for _cls, _table in ((SchoolLevel, school_levels), (Grade, grades), (SchoolClass, classes), (ClassMember, class_members)):
        mapper_registry.map_imperatively(_cls, _table)
