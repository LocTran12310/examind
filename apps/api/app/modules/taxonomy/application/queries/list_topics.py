from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.dto import TopicView
from app.modules.taxonomy.application.ports import TopicReader
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class ListTopics:
    subject_id: uuid.UUID | None = None


class ListTopicsHandler:
    """The whole tree of the org (or one subject) as a flat list: a tree, not a paged list."""

    def __init__(self, reader: TopicReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: ListTopics) -> list[TopicView]:
        return self.reader.tree(actor.org_id, query.subject_id)
