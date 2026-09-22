"""Column filter operators (symbol convention) and business-day bounds (ui-standards AC-02, AC-05)."""
from datetime import UTC, date, datetime

from sqlalchemy import update

from app.core.timezone import business_date, day_end_exclusive, day_start
from app.models import User
from tests.factories import login_as, make_user


def names(client, **filters):
    body = {"limit": 100, "filters": filters}
    return sorted(u["username"] for u in client.post("/api/users/search", json=body).json()["data"] if u["username"].startswith("hs"))


def test_business_day_is_vietnamese_whatever_the_server_zone():
    assert day_start(date(2026, 9, 22)) == datetime(2026, 9, 21, 17, 0, tzinfo=UTC)
    assert day_end_exclusive(date(2026, 9, 22)) == datetime(2026, 9, 22, 17, 0, tzinfo=UTC)
    assert business_date(datetime(2026, 9, 21, 18, 30, tzinfo=UTC)) == date(2026, 9, 22)  # 01:30 in Hà Nội
    assert business_date(datetime(2026, 9, 21, 18, 30)) == date(2026, 9, 22)  # naive = UTC


def test_text_number_and_date_operators(client, db):
    admin = login_as(client, db, "org_admin")
    for u, name in (("hs01", "Nguyễn Văn An"), ("hs02", "Trần An Bình"), ("hs03", "Lê Thị Hoa")):
        make_user(db, admin.organization, u, full_name=name)
    db.commit()
    assert names(client, full_name={"value": "an"}) == ["hs01", "hs02"]  # * contains (default), accent-free
    assert names(client, full_name={"value": "nguyen", "operator": "+"}) == ["hs01"]
    assert names(client, full_name={"value": "hoa", "operator": "-"}) == ["hs03"]
    assert names(client, full_name={"value": "le thi hoa", "operator": "="}) == ["hs03"]
    assert names(client, full_name={"value": "an", "operator": "!"}) == ["hs03"]
    assert client.post("/api/users/search", json={"filters": {"full_name": {"value": "a", "operator": "~"}}}).status_code == 422
    # a user created 00:30 Hà Nội time on 22/09 is on the 22nd, not the 21st (UTC)
    db.execute(update(User).where(User.username == "hs01").values(created_at=datetime(2026, 9, 21, 17, 30, tzinfo=UTC)))
    db.execute(update(User).where(User.username == "hs02").values(created_at=datetime(2026, 9, 21, 16, 30, tzinfo=UTC)))
    db.execute(update(User).where(User.username == "hs03").values(created_at=datetime(2026, 9, 23, 3, 0, tzinfo=UTC)))
    db.commit()
    assert names(client, created_at={"value": "2026-09-22"}) == ["hs01"]
    assert names(client, created_at={"value": "2026-09-22", "operator": "<"}) == ["hs02"]
    assert names(client, created_at={"value": "2026-09-22", "operator": "<="}) == ["hs01", "hs02"]
    assert names(client, created_at={"value": "2026-09-22", "operator": ">"}) == ["hs03"]
    assert names(client, created_at={"from": "2026-09-22", "to": "2026-09-23"}) == ["hs01", "hs03"]
    assert client.post("/api/users/search", json={"filters": {"created_at": {"value": "2026-09-22", "operator": "!"}}}).status_code == 422


def test_number_operators(client, db):
    login_as(client, db, "org_admin")
    for name, grade in (("10A1", 10), ("11A1", 11), ("12A1", 12)):
        client.post("/api/classes", json={"name": name, "grade": grade})
    got = lambda **f: sorted(c["name"] for c in client.post("/api/classes/search", json={"filters": {"grade": f}}).json()["data"])  # noqa: E731
    assert got(value=11) == ["11A1"]
    assert got(value=11, operator=">=") == ["11A1", "12A1"]
    assert got(value=11, operator="<") == ["10A1"]
