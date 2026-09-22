from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._topics import load_topic
from app.modules.taxonomy.domain.ports import TopicReferences, TopicRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteTopic:
    topic_id: uuid.UUID


class DeleteTopicHandler:
    """Only a leaf nobody refers to; otherwise delete/merge the children or merge the node first."""

    def __init__(self, topics: TopicRepository, references: TopicReferences, audit: AuditTrail, uow: UnitOfWork):
        self.topics, self.references, self.audit, self.uow = topics, references, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteTopic) -> None:
        t = load_topic(self.topics, actor.org_id, cmd.topic_id)
        if self.topics.has_children(t.id):
            raise Conflict("Chuyên đề còn nhánh con — hãy xóa hoặc gộp nhánh con trước", code="topic_has_children")
        if self.references.count(actor.org_id, [t.id]):
            raise Conflict("Chuyên đề đang được gắn cho câu hỏi — hãy gộp vào chuyên đề khác", code="topic_in_use")
        self.topics.remove(t)
        self.audit.record(actor, actor.org_id, "topic.delete", "topic", t.id, name=t.name)
        self.uow.commit()
