"""Server-side list queries for data tables (ui-shadcn-shell ADR-03).

A list endpoint declares its columns once — which can be searched with `q`, filtered by a query
parameter of the same name, and sorted — and `paginate` turns the request's `q`, column filters,
`sort` and `page`/`page_size` into SQL. The browser never filters rows itself (ADR-02).

Filter kinds (ui-standards ADR-01: operators sent as `<col>_op`):
- text    `?full_name=bui[&full_name_op=*]`  accent/case-insensitive; ops `*` contains (default),
          `=` equals, `+` starts with, `-` ends with, `!` does not contain
- exact   `?role=student`             equality; comma list = IN (`?status=active,suspended`)
- bool    `?is_active=true`
- number  `?grade=10[&grade_op=>=]`   ops `=` (default) `<` `<=` `>` `>=`; also `grade_min` / `grade_max`
- date    timestamps: `?created_at=2026-09-22[&created_at_op=<]` with the number ops, or a range
          `?created_at_from=…&created_at_to=…` (inclusive days). Days are business days (Asia/Ho_Chi_Minh)
          turned into UTC bounds [00:00, next 00:00).
- day     date columns (no time): same params, compared as calendar dates.
"""
from dataclasses import dataclass
from datetime import date
import uuid

from fastapi import Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement, Select

from app.core.errors import AppError

MAX_ALL = 1000
PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 200


@dataclass
class Col:
    expr: ColumnElement
    kind: str = "text"  # text | exact | bool | date | number | uuid
    sortable: bool = True
    filterable: bool = True


@dataclass
class ListParams:
    q: str
    sort: str
    page: int
    page_size: int
    filters: dict[str, str]


def list_params(request: Request, q: str = "", sort: str = "", page: int = Query(1, ge=1),
                page_size: str = Query(str(PAGE_SIZE_DEFAULT), pattern=r"^(\d{1,4}|all)$")) -> ListParams:
    """FastAPI dependency: the common params plus every other query param as a candidate column filter."""
    size = MAX_ALL if page_size == "all" else max(1, min(int(page_size), PAGE_SIZE_MAX))
    if page_size == "all":
        page = 1
    reserved = {"q", "sort", "page", "page_size"}
    filters = {k: v for k, v in request.query_params.items() if k not in reserved and v != ""}
    return ListParams(q=q.strip(), sort=sort.strip(), page=page, page_size=size, filters=filters)


from app.shared.application.search import COMPARE_OPS, TEXT_OPS  # noqa: E402
from app.shared.infrastructure.sql_search import compare_clause as _compare, contains as _contains, day_clause, text_clause as _text  # noqa: E402,F401


def _bad(field: str, message: str) -> AppError:
    return AppError("bad_filter", message, 422, {field: message})


def _parse_date(field: str, value: str) -> date:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        raise _bad(field, "Ngày không hợp lệ (yyyy-mm-dd)")


def _number(field: str, value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise _bad(field, "Giá trị số không hợp lệ")


def _day(e, d: date, op: str, suffix: str, timestamp: bool):
    return day_clause(e, d, op, suffix.lstrip("_"), timestamp)


def _filter_clauses(cols: dict[str, Col], filters: dict[str, str]) -> list:
    ops: dict[str, str] = {}
    for key, value in filters.items():
        if key.endswith("_op") and key[:-3] in cols:
            ops[key[:-3]] = value
    clauses = []
    for key, value in filters.items():
        if key.endswith("_op") and key[:-3] in cols:
            continue
        base, suffix = key, ""
        for s in ("_from", "_to", "_min", "_max"):
            if key.endswith(s) and key[: -len(s)] in cols:
                base, suffix = key[: -len(s)], s
                break
        col = cols.get(base)
        if col is None or not col.filterable:
            continue  # endpoint-specific params (e.g. class_id) are handled by the caller
        e, kind = col.expr, col.kind
        op = ops.get(base)
        if kind == "text":
            op = op or "*"
            if op not in TEXT_OPS:
                raise _bad(f"{base}_op", "Kiểu lọc không hợp lệ")
            clauses.append(_text(e, value, op))
        elif kind in ("exact", "uuid"):
            parts = [p for p in value.split(",") if p]
            if kind == "uuid":
                try:
                    parts = [uuid.UUID(p) for p in parts]
                except ValueError:
                    raise _bad(key, "Mã không hợp lệ")
            clauses.append(e == parts[0] if len(parts) == 1 else e.in_(parts))
        elif kind == "bool":
            clauses.append(e.is_(value.lower() in ("1", "true", "yes", "on")))
        elif kind in ("date", "day"):
            op = op or "="
            if op not in COMPARE_OPS:
                raise _bad(f"{base}_op", "Kiểu lọc không hợp lệ")
            clauses.append(_day(e, _parse_date(key, value), op, suffix, kind == "date"))
        elif kind == "number":
            n = _number(key, value)
            if suffix:
                clauses.append(e >= n if suffix == "_min" else e <= n)
            else:
                op = op or "="
                if op not in COMPARE_OPS:
                    raise _bad(f"{base}_op", "Kiểu lọc không hợp lệ")
                clauses.append(_compare(e, n, op))
    return clauses


def _order(cols: dict[str, Col], sort: str, default: list) -> list:
    if not sort:
        return default
    out = []
    for part in sort.split(","):
        part = part.strip()
        desc = part.startswith("-")
        name = part.lstrip("-+")
        col = cols.get(name)
        if col is None or not col.sortable:
            raise AppError("bad_sort", f"Không sắp xếp được theo '{name}'", 422, {"sort": name})
        out.append(col.expr.desc().nulls_last() if desc else col.expr.asc().nulls_last())
    return out + default


def paginate(db: Session, stmt: Select, params: ListParams, cols: dict[str, Col], *, search: list | None = None,
             default_sort: list | None = None, scalars: bool = True):
    """Apply q / column filters / sort / paging. Returns (rows, total)."""
    if params.q and search:
        stmt = stmt.where(or_(*[_contains(e, params.q) for e in search]))
    for c in _filter_clauses(cols, params.filters):
        stmt = stmt.where(c)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    stmt = stmt.order_by(None).order_by(*_order(cols, params.sort, default_sort or []))
    stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    rows = db.scalars(stmt).all() if scalars else db.execute(stmt).all()
    return rows, total
