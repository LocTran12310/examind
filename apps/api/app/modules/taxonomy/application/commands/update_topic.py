from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._topics import load_topic
from app.modules.taxonomy.application.dto import TopicView, topic_view
from app.modules.taxonomy.domain.ports import TopicRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateTopic:
    topic_id: uuid.UUID
    name: str | None = None
    level_kind: str | None = None
    grade: int | None = None
    sort: int | None = None


class UpdateTopicHandler:
    """Rename / re-kind a node; its path (and so its place in the tree) does not change."""

    def __init__(self, topics: TopicRepository, uow: UnitOfWork):
        self.topics, self.uow = topics, uow

    def __call__(self, actor: Actor, cmd: UpdateTopic) -> TopicView:
        t = load_topic(self.topics, actor.org_id, cmd.topic_id)
        t.change(cmd.name, cmd.level_kind, cmd.grade, cmd.sort)
        self.uow.commit()
        return topic_view(t)
