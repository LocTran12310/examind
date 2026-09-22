"""School years and HK1/HK2 terms (school-years ADR-01, A-01…A-04)."""
from datetime import date, datetime
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, conflict, forbidden, not_found, validation
from app.core.timezone import business_date, business_today
from app.deps import OrgScope
from app.models import SchoolClass, SchoolTerm, SchoolYear
from app.models.school_year import TERMS
from app.services import audit
from app.services.paging import Col, ListParams, paginate

CODE_RE = re.compile(r"^(\d{4})-(\d{4})$")
STATUS_LABEL = {"planning": "Chuẩn bị", "active": "Đang học", "closed": "Đã khóa"}


def _admin(scope: OrgScope) -> None:
    if scope.role != "org_admin":
        raise forbidden()


def current_code(today: date | None = None) -> str:
    d = today or business_today()
    y = d.year if d.month >= 8 else d.year - 1
    return f"{y}-{y + 1}"


def default_dates(code: str) -> tuple[date, date, list[tuple[str, str, date, date]]]:
    a, b = (int(x) for x in code.split("-"))
    start, end = date(a, 9, 5), date(b, 5, 31)
    terms = [("hk1", "Học kỳ 1", start, date(b, 1, 15)), ("hk2", "Học kỳ 2", date(b, 1, 16), end)]
    return start, end, terms


def _check_code(code: str) -> str:
    m = CODE_RE.match((code or "").strip())
    if not m or int(m.group(2)) != int(m.group(1)) + 1:
        raise validation("Năm học dạng 2026-2027", "code")
    return m.group(0)


def get_year(db: Session, scope: OrgScope, year_id) -> SchoolYear:
    y = db.get(SchoolYear, year_id)
    if y is None or y.organization_id != scope.org_id:
        raise not_found("Không tìm thấy năm học")
    return y


def active_year(db: Session, org_id) -> SchoolYear | None:
    return db.scalar(select(SchoolYear).where(SchoolYear.organization_id == org_id, SchoolYear.status == "active"))


def year_for_date(db: Session, org_id, when: date | datetime) -> SchoolYear | None:
    d = business_date(when)
    return db.scalar(select(SchoolYear).where(SchoolYear.organization_id == org_id, SchoolYear.start_date <= d, SchoolYear.end_date >= d)
                     .order_by(SchoolYear.start_date.desc()).limit(1))


def term_for_date(year: SchoolYear | None, when: date | datetime) -> str | None:
    if year is None:
        return None
    d = business_date(when)
    for t in year.terms:
        if t.start_date <= d <= t.end_date:
            return t.code
    return None


def ensure_year(db: Session, org_id, code: str, actor=None) -> SchoolYear:
    """The org's year with this code, created (with HK1/HK2) when missing — classes and imports rely on it."""
    code = _check_code(code)
    y = db.scalar(select(SchoolYear).where(SchoolYear.organization_id == org_id, SchoolYear.code == code))
    if y is not None:
        return y
    start, end, terms = default_dates(code)
    status = "active" if code == current_code() and active_year(db, org_id) is None else "planning"
    y = SchoolYear(organization_id=org_id, code=code, name=f"Năm học {code}", start_date=start, end_date=end, status=status,
                   terms=[SchoolTerm(code=c, name=n, start_date=s, end_date=e) for c, n, s, e in terms])
    db.add(y)
    db.flush()
    if actor is not None:
        audit.record(db, actor, org_id, "year.create", "school_year", y.id, code=code)
    return y


CLASS_COUNT = select(func.count(SchoolClass.id)).where(SchoolClass.school_year_id == SchoolYear.id).correlate(SchoolYear).scalar_subquery()
YEAR_COLS = {"code": Col(SchoolYear.code), "name": Col(SchoolYear.name), "status": Col(SchoolYear.status, "exact"),
             "start_date": Col(SchoolYear.start_date, "day"), "class_count": Col(CLASS_COUNT, filterable=False)}


def list_years(db: Session, scope: OrgScope, params: ListParams):
    stmt = select(SchoolYear, CLASS_COUNT).where(SchoolYear.organization_id == scope.org_id)
    return paginate(db, stmt, params, YEAR_COLS, search=[SchoolYear.code, SchoolYear.name], scalars=False,
                    default_sort=[SchoolYear.start_date.desc()])


def _apply_terms(y: SchoolYear, terms: list[dict] | None) -> None:
    if not terms:
        return
    by_code = {t.code: t for t in y.terms}
    for t in terms:
        code = t.get("code")
        if code not in dict(TERMS):
            raise validation("Chỉ có Học kỳ 1 và Học kỳ 2", "terms")
        row = by_code.get(code)
        if row is None:
            row = SchoolTerm(code=code, name=dict(TERMS)[code], start_date=t["start_date"], end_date=t["end_date"])
            y.terms.append(row)
        else:
            row.start_date, row.end_date = t.get("start_date") or row.start_date, t.get("end_date") or row.end_date
    for t in y.terms:
        if not (y.start_date <= t.start_date <= t.end_date <= y.end_date):
            raise validation(f"{t.name} phải nằm trong năm học và ngày bắt đầu trước ngày kết thúc", "terms")


def create_year(db: Session, scope: OrgScope, code: str, name: str | None = None, start_date=None, end_date=None, terms=None) -> SchoolYear:
    _admin(scope)
    code = _check_code(code)
    if db.scalar(select(SchoolYear.id).where(SchoolYear.organization_id == scope.org_id, SchoolYear.code == code)):
        raise conflict("Năm học đã tồn tại", "code")
    s, e, default_terms = default_dates(code)
    y = SchoolYear(organization_id=scope.org_id, code=code, name=(name or "").strip() or f"Năm học {code}",
                   start_date=start_date or s, end_date=end_date or e, status="planning",
                   terms=[SchoolTerm(code=c, name=n, start_date=ts, end_date=te) for c, n, ts, te in default_terms])
    if y.start_date >= y.end_date:
        raise validation("Ngày bắt đầu phải trước ngày kết thúc", "end_date")
    if start_date or end_date:  # custom year bounds: stretch the default terms to them
        y.terms[0].start_date, y.terms[-1].end_date = y.start_date, y.end_date
    _apply_terms(y, terms)
    db.add(y)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "year.create", "school_year", y.id, code=code)
    return y


def _audit_year(db, scope, y: SchoolYear, action: str, **data) -> None:
    audit.record(db, scope.user, scope.org_id, action, "school_year", y.id, code=y.code, closed_year=y.status == "closed", **data)


def update_year(db: Session, scope: OrgScope, year_id, name=None, start_date=None, end_date=None, terms=None) -> SchoolYear:
    _admin(scope)
    y = get_year(db, scope, year_id)
    before = {"name": y.name, "start_date": str(y.start_date), "end_date": str(y.end_date)}
    if name:
        y.name = name.strip()
    y.start_date, y.end_date = start_date or y.start_date, end_date or y.end_date
    if y.start_date >= y.end_date:
        raise validation("Ngày bắt đầu phải trước ngày kết thúc", "end_date")
    _apply_terms(y, terms)
    after = {"name": y.name, "start_date": str(y.start_date), "end_date": str(y.end_date)}
    _audit_year(db, scope, y, "year.update", changes={k: [before[k], after[k]] for k in after if before[k] != after[k]}, terms=bool(terms))
    return y


def set_status(db: Session, scope: OrgScope, year_id, status: str) -> SchoolYear:
    """activate: this year becomes the only active one (the previous active year is closed); close; reopen → planning."""
    _admin(scope)
    y = get_year(db, scope, year_id)
    if status == "active":
        prev = active_year(db, scope.org_id)
        if prev is not None and prev.id != y.id:
            prev.status = "closed"
            db.flush()
            _audit_year(db, scope, prev, "year.close", reason="another year activated")
        y.status = "active"
        db.flush()
        _audit_year(db, scope, y, "year.activate")
    elif status == "closed":
        y.status = "closed"
        _audit_year(db, scope, y, "year.close")
    elif status == "planning":
        was = y.status
        y.status = "planning"
        _audit_year(db, scope, y, "year.reopen", was=was)
    else:
        raise validation("Trạng thái không hợp lệ", "status")
    return y


def delete_year(db: Session, scope: OrgScope, year_id) -> None:
    _admin(scope)
    y = get_year(db, scope, year_id)
    n = db.scalar(select(func.count()).select_from(SchoolClass).where(SchoolClass.school_year_id == y.id))
    if n:
        raise AppError("in_use", f"Năm học còn {n} lớp", 409)
    if y.status == "active":
        raise AppError("in_use", "Không xóa được năm học đang học", 409)
    db.delete(y)
    audit.record(db, scope.user, scope.org_id, "year.delete", "school_year", y.id, code=y.code)
