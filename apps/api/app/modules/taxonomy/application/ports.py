from typing import Protocol
import uuid

from app.modules.taxonomy.application.dto import TagView
from app.shared.application.search import Page, SearchRequest


class TagReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest, subject: str | None, include_shared: bool) -> Page[TagView]:
        """`subject`: a subject id (its tags + shared ones unless include_shared is false), "shared", or None (all)."""
        ...
