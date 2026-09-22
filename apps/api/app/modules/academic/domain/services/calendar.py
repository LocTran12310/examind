"""School-year calendar rules (school-years ADR-01, A-01…A-04): a year runs 05/09 – 31/05, HK1 until 15/01."""
from datetime import date
import re

from app.modules.academic.domain.entities import TERMS, SchoolTerm, SchoolYear
from app.shared.domain.errors import Invalid

CODE_RE = re.compile(r"^(\d{4})-(\d{4})$")
STATUS_LABEL = {"planning": "Chuẩn bị", "active": "Đang học", "closed": "Đã khóa"}


def current_code(today: date) -> str:
    """The school year of a business day: a new year starts in August."""
    y = today.year if today.month >= 8 else today.year - 1
    return f"{y}-{y + 1}"


def default_dates(code: str) -> tuple[date, date, list[tuple[str, str, date, date]]]:
    a, b = (int(x) for x in code.split("-"))
    start, end = date(a, 9, 5), date(b, 5, 31)
    terms = [("hk1", "Học kỳ 1", start, date(b, 1, 15)), ("hk2", "Học kỳ 2", date(b, 1, 16), end)]
    return start, end, terms


def is_year_code(code: str | None) -> bool:
    m = CODE_RE.match((code or "").strip())
    return bool(m) and int(m.group(2)) == int(m.group(1)) + 1


def check_code(code: str, field: str = "code") -> str:
    if not is_year_code(code):
        raise Invalid("Năm học dạng 2026-2027", field)
    return code.strip()


def term_for_date(year, day: date) -> str | None:
    if year is None:
        return None
    for t in year.terms:
        if t.start_date <= day <= t.end_date:
            return t.code
    return None


def new_year(org_id, code: str, name: str | None = None, start: date | None = None, end: date | None = None,
             status: str = "planning") -> SchoolYear:
    """A year with HK1/HK2 on the default dates; custom bounds stretch the first and last term to them."""
    s, e, terms = default_dates(code)
    y = SchoolYear(organization_id=org_id, code=code, name=(name or "").strip() or f"Năm học {code}", start_date=start or s,
                   end_date=end or e, status=status,
                   terms=[SchoolTerm(code=c, name=n, start_date=ts, end_date=te) for c, n, ts, te in terms])
    check_bounds(y)
    if start or end:
        y.terms[0].start_date, y.terms[-1].end_date = y.start_date, y.end_date
    return y


def check_bounds(y: SchoolYear) -> None:
    if y.start_date >= y.end_date:
        raise Invalid("Ngày bắt đầu phải trước ngày kết thúc", "end_date")


def apply_terms(y: SchoolYear, terms: list[dict] | None) -> None:
    """Change HK1/HK2 dates (a missing term is added); every term must stay inside the year."""
    if not terms:
        return
    names = dict(TERMS)
    by_code = {t.code: t for t in y.terms}
    for t in terms:
        code = t.get("code")
        if code not in names:
            raise Invalid("Chỉ có Học kỳ 1 và Học kỳ 2", "terms")
        row = by_code.get(code)
        if row is None:
            y.terms.append(SchoolTerm(code=code, name=names[code], start_date=t["start_date"], end_date=t["end_date"]))
        else:
            row.start_date, row.end_date = t.get("start_date") or row.start_date, t.get("end_date") or row.end_date
    for t in y.terms:
        if not (y.start_date <= t.start_date <= t.end_date <= y.end_date):
            raise Invalid(f"{t.name} phải nằm trong năm học và ngày bắt đầu trước ngày kết thúc", "terms")
