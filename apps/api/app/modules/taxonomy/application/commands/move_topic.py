from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._topics import load_topic, move
from app.modules.taxonomy.application.dto import TopicView, topic_view
from app.modules.taxonomy.domain.ports import TopicRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class MoveTopic:
    topic_id: uuid.UUID
    parent_id: uuid.UUID | None  # None = root


class MoveTopicHandler:
    def __init__(self, topics: TopicRepository, audit: AuditTrail, uow: UnitOfWork):
        self.topics, self.audit, self.uow = topics, audit, uow

    def __call__(self, actor: Actor, cmd: MoveTopic) -> TopicView:
        t = load_topic(self.topics, actor.org_id, cmd.topic_id)
        parent = load_topic(self.topics, actor.org_id, cmd.parent_id) if cmd.parent_id else None
        move(self.topics, self.audit, actor, t, parent)
        self.uow.commit()
        return topic_view(t)
