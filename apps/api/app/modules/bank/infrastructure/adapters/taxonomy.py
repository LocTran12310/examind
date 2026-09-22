"""Taxonomy over the taxonomy context's application API. The API object is handed in by the composition root:
the bank never imports another module."""
from typing import Protocol
import uuid


class _TaxonomyApi(Protocol):
    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]: ...

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]: ...

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...


class TaxonomyAdapter:
    def __init__(self, taxonomy: _TaxonomyApi):
        self.taxonomy = taxonomy

    def topic_paths(self, org_id: uuid.UUID, topic_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        return self.taxonomy.topic_paths(org_id, topic_ids)

    def tag_groups(self, org_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        return self.taxonomy.tag_groups(org_id, tag_ids)

    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self.taxonomy.subject_exists(org_id, subject_id)
