"""What other contexts may ask the taxonomy context (architecture-refactor ADR-01)."""
import uuid

from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.domain.ports import SubjectLookup, TagRepository, TopicRepository


class TaxonomyApi:
    def __init__(self, topics: TopicRepository, tags: TagRepository, subjects: SubjectLookup):
        self.topics, self.tags, self.subjects = topics, tags, subjects

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{topic_id: ltree path} for the topics of the org among `topic_ids`; unknown or foreign ids are left out."""
        return self.topics.paths(org_id, list(topic_ids))

    def topic_labels(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str, str]]:
        """{topic_id: (name, ltree path)} for the topics of the org among `topic_ids`; unknown or foreign ids are left out."""
        return self.topics.labels(org_id, list(topic_ids))

    def topic_subjects(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID]:
        """{topic_id: subject_id} for the topics of the org among `topic_ids`; unknown or foreign ids are left out."""
        return self.topics.subject_ids(org_id, list(topic_ids))

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{tag_id: group} for the tags of the org among `tag_ids`; unknown or foreign ids are left out."""
        return self.tags.groups(org_id, list(tag_ids))

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self.subjects.exists(org_id, subject_id)

    def grade_levels(self, org_id: uuid.UUID) -> set[int]:
        """The levels of the grades the org keeps (what a question's `grade` may be)."""
        return self.subjects.grade_levels(org_id)

    def source_tag(self, org_id: uuid.UUID, name: str) -> uuid.UUID:
        """The "source" tag (nguồn đề) of that name, case-insensitive; created when missing (flushed with the caller's
        transaction). Ingestion tags every question of a document with its source."""
        tag = self.tags.find(org_id, "source", name)
        if tag is None:
            tag = Tag(organization_id=org_id, group="source", name=name)
            self.tags.add(tag)
        return tag.id
