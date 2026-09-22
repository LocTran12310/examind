"""Maps the analytics dataclasses onto their tables (architecture-refactor ADR-01). Importing this module is enough;
mapping happens once."""
from app.modules.analytics.domain.entities import TopicMastery
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.analytics import student_topic_mastery

if not any(m.class_ is TopicMastery for m in mapper_registry.mappers):
    mapper_registry.map_imperatively(TopicMastery, student_topic_mastery)
