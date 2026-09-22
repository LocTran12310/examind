"""Column filter operators (the reference convention) and business-day bounds (ui-standards AC-02, AC-05)."""
from datetime import UTC, date, datetime

from sqlalchemy import update

from app.core.timezone import business_date, day_end_exclusive, day_start
from app.models import User
from tests.factories import login_as, make_user


def names(client, **params):
    return sorted(u["username"] for u in client.get("/api/users", params={"page_size": 100, **params}).json()["items"] if u["username"].startswith("hs"))


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
    assert names(client, full_name="an") == ["hs01", "hs02"]  # * contains (default), accent-free
    assert names(client, full_name="nguyen", full_name_op="+") == ["hs01"]
    assert names(client, full_name="hoa", full_name_op="-") == ["hs03"]
    assert names(client, full_name="le thi hoa", full_name_op="=") == ["hs03"]
    assert names(client, full_name="an", full_name_op="!") == ["hs03"]
    assert client.get("/api/users", params={"full_name": "a", "full_name_op": "~"}).status_code == 422
    # a user created 00:30 Hà Nội time on 22/09 is on the 22nd, not the 21st (UTC)
    db.execute(update(User).where(User.username == "hs01").values(created_at=datetime(2026, 9, 21, 17, 30, tzinfo=UTC)))
    db.execute(update(User).where(User.username == "hs02").values(created_at=datetime(2026, 9, 21, 16, 30, tzinfo=UTC)))
    db.execute(update(User).where(User.username == "hs03").values(created_at=datetime(2026, 9, 23, 3, 0, tzinfo=UTC)))
    db.commit()
    assert names(client, created_at="2026-09-22") == ["hs01"]
    assert names(client, created_at="2026-09-22", created_at_op="<") == ["hs02"]
    assert names(client, created_at="2026-09-22", created_at_op="<=") == ["hs01", "hs02"]
    assert names(client, created_at="2026-09-22", created_at_op=">") == ["hs03"]
    assert names(client, created_at_from="2026-09-22", created_at_to="2026-09-23") == ["hs01", "hs03"]
    assert client.get("/api/users", params={"created_at": "2026-09-22", "created_at_op": "!"}).status_code == 422


def test_number_operators(client, db):
    login_as(client, db, "org_admin")
    for name, grade in (("10A1", 10), ("11A1", 11), ("12A1", 12)):
        client.post("/api/classes", json={"name": name, "grade": grade})
    got = lambda **p: sorted(c["name"] for c in client.get("/api/classes", params=p).json()["items"])  # noqa: E731
    assert got(grade="11") == ["11A1"]
    assert got(grade="11", grade_op=">=") == ["11A1", "12A1"]
    assert got(grade="11", grade_op="<") == ["10A1"]
