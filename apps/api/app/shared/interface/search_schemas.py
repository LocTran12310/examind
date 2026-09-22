"""Request/response bodies of `POST /<resource>/search` (architecture-refactor ADR-03)."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.shared.application.search import LIMIT_ALL, LIMIT_DEFAULT, Filter, SearchRequest, SortKey

T = TypeVar("T")


class FilterIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    operator: str | None = None
    value: Any = None
    from_: Any = Field(None, alias="from")
    to: Any = None


class SortIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    desc: bool = False


class SearchBody(BaseModel):
    """Common body; a resource subclasses it to add its own scope parameters."""
    page: int = Field(1, ge=1)
    limit: int = Field(LIMIT_DEFAULT, ge=1, le=LIMIT_ALL)
    q: str = ""
    sort: list[SortIn] = []
    filters: dict[str, FilterIn] = {}

    def to_request(self) -> SearchRequest:
        return SearchRequest(
            page=self.page, limit=self.limit, q=self.q.strip(),
            sort=tuple(SortKey(s.field, s.desc) for s in self.sort),
            filters={k: Filter(v.operator, v.value, v.from_, v.to) for k, v in self.filters.items()},
        )


class PageOut(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    limit: int
