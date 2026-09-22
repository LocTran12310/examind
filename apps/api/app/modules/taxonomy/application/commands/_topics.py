import uuid

from app.modules.taxonomy.domain.ports import TopicRepository
from app.modules.taxonomy.domain.topics import Topic, topic_not_found
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail


def load_topic(topics: TopicRepository, org_id: uuid.UUID, topic_id: uuid.UUID) -> Topic:
    t = topics.get(org_id, topic_id)
    if t is None:
        raise topic_not_found()
    return t


def move(topics: TopicRepository, audit: AuditTrail, actor: Actor, t: Topic, parent: Topic | None) -> Topic:
    """Move `t` (and its subtree) under `parent`; None = make it a strand."""
    new_path = t.path_under(parent, topics.subtree_depth(t))
    topics.move(t, parent.id if parent else None, new_path)
    audit.record(actor, actor.org_id, "topic.move", "topic", t.id, to=str(parent.id) if parent else None)
    return t
