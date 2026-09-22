"""What other contexts may ask the taxonomy context (architecture-refactor ADR-01)."""
import uuid

from app.modules.taxonomy.domain.ports import SubjectLookup, TagRepository, TopicRepository


class TaxonomyApi:
    def __init__(self, topics: TopicRepository, tags: TagRepository, subjects: SubjectLookup):
        self.topics, self.tags, self.subjects = topics, tags, subjects

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{topic_id: ltree path} for the topics of the org among `topic_ids`; unknown or foreign ids are left out."""
        return self.topics.paths(org_id, list(topic_ids))

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{tag_id: group} for the tags of the org among `tag_ids`; unknown or foreign ids are left out."""
        return self.tags.groups(org_id, list(tag_ids))

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self.subjects.exists(org_id, subject_id)
