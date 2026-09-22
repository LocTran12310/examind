"""Subjects over the taxonomy context's application API (handed in by the composition root)."""
from typing import Protocol
import uuid


class _TaxonomyApi(Protocol):
    def subject_exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...


class TaxonomySubjects:
    def __init__(self, taxonomy: _TaxonomyApi):
        self.taxonomy = taxonomy

    def exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return self.taxonomy.subject_exists(org_id, subject_id)
