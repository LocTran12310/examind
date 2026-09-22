"""Maps the bank dataclasses onto their tables (architecture-refactor ADR-01). Importing this module is enough;
mapping happens once."""
from app.modules.bank.domain.entities import Question, QuestionTag, QuestionTopic, ReviewEvent
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.bank import question_tags, question_topics, questions, review_events


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


for _cls, _table in ((Question, questions), (QuestionTopic, question_topics), (QuestionTag, question_tags), (ReviewEvent, review_events)):
    if not _mapped(_cls):
        mapper_registry.map_imperatively(_cls, _table)
