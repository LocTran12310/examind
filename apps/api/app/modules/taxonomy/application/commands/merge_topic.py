from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._topics import load_topic, move
from app.modules.taxonomy.application.dto import TopicView, topic_view
from app.modules.taxonomy.domain.ports import TopicReferences, TopicRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class MergeTopic:
    topic_id: uuid.UUID
    target_id: uuid.UUID


class MergeTopicHandler:
    """Children and references of the source move to the target, then the source is deleted."""

    def __init__(self, topics: TopicRepository, references: TopicReferences, audit: AuditTrail, uow: UnitOfWork):
        self.topics, self.references, self.audit, self.uow = topics, references, audit, uow

    def __call__(self, actor: Actor, cmd: MergeTopic) -> TopicView:
        src = load_topic(self.topics, actor.org_id, cmd.topic_id)
        target = load_topic(self.topics, actor.org_id, cmd.target_id)
        src.check_merge_into(target)
        for child in self.topics.children(src.id):
            move(self.topics, self.audit, actor, child, target)
        self.references.repoint(actor.org_id, src.id, target.id)
        name = src.name
        self.topics.remove(src)
        self.audit.record(actor, actor.org_id, "topic.merge", "topic", target.id, merged=str(src.id), name=name)
        self.uow.commit()
        return topic_view(target)
