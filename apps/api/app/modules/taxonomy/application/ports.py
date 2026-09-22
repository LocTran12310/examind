from typing import Protocol
import uuid

from app.modules.taxonomy.application.dto import TagView, TaxonomyView, TopicView
from app.shared.application.search import Page, SearchRequest


class TagReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, subject: str | None, include_shared: bool) -> Page[TagView]:
        """`subject`: a subject id (its tags + shared ones unless include_shared is false), "shared", or None (all)."""
        ...


class TopicReader(Protocol):
    def tree(self, org_id: uuid.UUID, subject_id: uuid.UUID | None) -> list[TopicView]:
        """Every node (of one subject), by path, with its number of direct children."""
        ...


class TaxonomyReader(Protocol):
    def get(self, org_id: uuid.UUID) -> TaxonomyView: ...
