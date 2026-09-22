"""The search contract every list uses (architecture-refactor ADR-03).

A filter is read by the kind of the column it targets:
- text                  `{operator: * = + - !, value}`   (`*` contains is the default)
- number / date / day   `{operator: = < <= > >=, value}` or a range `{from, to}` (inclusive)
- enum / uuid / bool    `{value}`; a list means "any of"
"""
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

TEXT_OPS = ("*", "=", "+", "-", "!")
COMPARE_OPS = ("=", "<", "<=", ">", ">=")
LIMIT_DEFAULT = 20
LIMIT_MAX = 200
LIMIT_ALL = 1000  # pickers ask for "everything" (bounded)


@dataclass(frozen=True)
class Filter:
    operator: str | None = None
    value: Any = None
    from_: Any = None
    to: Any = None


@dataclass(frozen=True)
class SortKey:
    field: str
    desc: bool = False


@dataclass(frozen=True)
class SearchRequest:
    page: int = 1
    limit: int = LIMIT_DEFAULT
    q: str = ""
    sort: tuple[SortKey, ...] = ()
    filters: dict[str, Filter] = field(default_factory=dict)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


@dataclass
class Page(Generic[T]):
    data: list[T]
    total: int
    page: int
    limit: int
