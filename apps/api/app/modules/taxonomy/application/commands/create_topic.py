from dataclasses import dataclass
import uuid

from app.modules.taxonomy.application.commands._topics import load_topic
from app.modules.taxonomy.application.dto import TopicView, topic_view
from app.modules.taxonomy.domain.ports import SubjectLookup, TopicRepository
from app.modules.taxonomy.domain.topics import Topic, clean_topic_name
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class CreateTopic:
    name: str
    subject_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    level_kind: str | None = None
    grade: int | None = None


class CreateTopicHandler:
    def __init__(self, topics: TopicRepository, subjects: SubjectLookup, audit: AuditTrail, uow: UnitOfWork):
        self.topics, self.subjects, self.audit, self.uow = topics, subjects, audit, uow

    def __call__(self, actor: Actor, cmd: CreateTopic) -> TopicView:
        name = clean_topic_name(cmd.name)
        parent = load_topic(self.topics, actor.org_id, cmd.parent_id) if cmd.parent_id else None
        subject_id = parent.subject_id if parent else cmd.subject_id  # a child always lives in its parent's subject
        if subject_id is None or not self.subjects.exists(actor.org_id, subject_id):
            raise Invalid("Môn học không hợp lệ", "subject_id")
        t = Topic.create(actor.org_id, subject_id, name, parent, cmd.level_kind, cmd.grade,
                         sort=self.topics.next_sort(actor.org_id, parent.id if parent else None))
        self.topics.add(t)
        self.audit.record(actor, actor.org_id, "topic.create", "topic", t.id, name=t.name)
        self.uow.commit()
        return topic_view(t)
