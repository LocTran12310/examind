"""SearchRequest → SQL: typed filters, sort, paging (architecture-refactor ADR-03).

A resource declares its columns once (`Col`: expression, kind, sortable, filterable); `search` applies
`q` over the search expressions, each filter by the column kind, the sort keys, then offset/limit.
Text matching ignores accents and case (`f_unaccent`); days are business days (Asia/Ho_Chi_Minh)
turned into UTC bounds [00:00, next 00:00).
"""
from dataclasses import dataclass
from datetime import date, timedelta
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement, Select

from app.core.timezone import day_end_exclusive, day_start
from app.shared.application.search import COMPARE_OPS, TEXT_OPS, Filter, SearchRequest
from app.shared.domain.errors import Invalid

KINDS = ("text", "exact", "uuid", "bool", "number", "date", "day")


@dataclass
class Col:
    expr: ColumnElement
    kind: str = "text"  # text | exact | uuid | bool | number | date (timestamp) | day (date column)
    sortable: bool = True
    filterable: bool = True


def bad_filter(field: str, message: str) -> Invalid:
    return Invalid(message, field, code="bad_filter")


def unaccent(expr):
    return func.f_unaccent(expr)


def like_escape(value: str) -> str:
    return value.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def contains(expr, value: str):
    return unaccent(expr).ilike(func.f_unaccent("%" + like_escape(value) + "%"))


def text_clause(e, value: str, op: str):
    folded = unaccent(e)
    needle = like_escape(value)
    if op == "=":
        return func.lower(folded) == func.lower(func.f_unaccent(value.strip()))
    if op == "+":
        return folded.ilike(func.f_unaccent(needle + "%"))
    if op == "-":
        return folded.ilike(func.f_unaccent("%" + needle))
    if op == "!":
        return or_(e.is_(None), ~folded.ilike(func.f_unaccent("%" + needle + "%")))
    return folded.ilike(func.f_unaccent("%" + needle + "%"))


def compare_clause(e, v, op: str):
    return {"=": e == v, "<": e < v, "<=": e <= v, ">": e > v, ">=": e >= v}[op]


def day_clause(e, d: date, op: str, bound: str = "", timestamp: bool = True):
    """A business day against a timestamp (UTC bounds) or a date column. `bound`: "from" / "to" of a range."""
    lo, hi = (day_start(d), day_end_exclusive(d)) if timestamp else (d, d + timedelta(days=1))
    if bound == "from":
        return e >= lo
    if bound == "to":
        return e < hi
    return {"=": and_(e >= lo, e < hi), "<": e < lo, "<=": e < hi, ">": e >= hi, ">=": e >= lo}[op]


def parse_day(field: str, value) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise bad_filter(field, "Ngày không hợp lệ (yyyy-mm-dd)")


def parse_number(field: str, value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise bad_filter(field, "Giá trị số không hợp lệ")


def _values(value) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [v for v in value if v not in (None, "")]
    return [v for v in str(value).split(",") if v] if isinstance(value, str) else [value]


def _truthy(value) -> bool:
    return value if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on")


def filter_clause(name: str, col: Col, f: Filter):
    """One clause for one filter, or None when the filter is empty."""
    e, kind = col.expr, col.kind
    if kind == "text":
        if f.value in (None, ""):
            return None
        op = f.operator or "*"
        if op not in TEXT_OPS:
            raise bad_filter(name, "Kiểu lọc không hợp lệ")
        return text_clause(e, str(f.value), op)
    if kind in ("exact", "uuid"):
        parts = _values(f.value)
        if not parts:
            return None
        if kind == "uuid":
            try:
                parts = [p if isinstance(p, uuid.UUID) else uuid.UUID(str(p)) for p in parts]
            except ValueError:
                raise bad_filter(name, "Mã không hợp lệ")
        return e == parts[0] if len(parts) == 1 else e.in_(parts)
    if kind == "bool":
        return None if f.value in (None, "") else e.is_(_truthy(f.value))
    if kind in ("number", "date", "day"):
        parse = parse_number if kind == "number" else parse_day
        clauses = []
        if f.value not in (None, ""):
            op = f.operator or "="
            if op not in COMPARE_OPS:
                raise bad_filter(name, "Kiểu lọc không hợp lệ")
            v = parse(name, f.value)
            clauses.append(compare_clause(e, v, op) if kind == "number" else day_clause(e, v, op, timestamp=kind == "date"))
        for bound, raw in (("from", f.from_), ("to", f.to)):
            if raw in (None, ""):
                continue
            v = parse(name, raw)
            if kind == "number":
                clauses.append(e >= v if bound == "from" else e <= v)
            else:
                clauses.append(day_clause(e, v, "=", bound, timestamp=kind == "date"))
        return and_(*clauses) if clauses else None
    raise ValueError(f"unknown column kind {kind}")


def where_clauses(cols: dict[str, Col], filters: dict[str, Filter]) -> list:
    out = []
    for name, f in filters.items():
        col = cols.get(name)
        if col is None or not col.filterable:
            raise bad_filter(name, f"Không lọc được theo '{name}'")
        c = filter_clause(name, col, f)
        if c is not None:
            out.append(c)
    return out


def order_by(cols: dict[str, Col], req: SearchRequest, default: list) -> list:
    out = []
    for key in req.sort:
        col = cols.get(key.field)
        if col is None or not col.sortable:
            raise Invalid(f"Không sắp xếp được theo '{key.field}'", "sort", code="bad_sort")
        out.append(col.expr.desc().nulls_last() if key.desc else col.expr.asc().nulls_last())
    return out + default


def search(db: Session, stmt: Select, req: SearchRequest, cols: dict[str, Col], *, text: list | None = None,
           default_sort: list | None = None, scalars: bool = True):
    """Apply q / filters / sort / paging. Returns (rows, total)."""
    if req.q and text:
        stmt = stmt.where(or_(*[contains(e, req.q) for e in text]))
    for c in where_clauses(cols, req.filters):
        stmt = stmt.where(c)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    stmt = stmt.order_by(None).order_by(*order_by(cols, req, default_sort or []))
    stmt = stmt.offset(req.offset).limit(req.limit)
    rows = db.scalars(stmt).all() if scalars else db.execute(stmt).all()
    return rows, total
