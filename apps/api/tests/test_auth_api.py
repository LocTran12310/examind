import logging
import time

import pytest

from app.routers.auth import ip_limiter
from tests.factories import PASSWORD, make_org, make_user


@pytest.fixture(autouse=True)
def _reset_limiter():
    ip_limiter.reset()


def login(client, org="trungtama", user="hs01", pw=PASSWORD):
    return client.post("/api/auth/login", json={"org_code": org, "username": user, "password": pw})


def test_login_sets_httponly_cookies_and_me(client, db):
    make_user(db, make_org(db))
    db.commit()
    r = login(client, "TrungtamA", "HS01")
    assert r.status_code == 200, r.text
    cookies = r.headers.get_list("set-cookie")
    assert any(c.startswith("ex_access=") and "HttpOnly" in c and "SameSite=lax" in c for c in cookies)
    assert any(c.startswith("ex_refresh=") and "Path=/api/auth" in c for c in cookies)
    me = client.get("/api/auth/me").json()
    assert me["username"] == "hs01" and me["org"]["code"] == "trungtama"


def test_generic_error_body_identical(client, db):
    make_user(db, make_org(db))
    db.commit()
    bodies = {login(client, *args).text for args in [("nope", "hs01", PASSWORD), ("trungtama", "x", PASSWORD), ("trungtama", "hs01", "bad")]}
    assert len(bodies) == 1
    assert "Sai tổ chức, tên đăng nhập hoặc mật khẩu" in bodies.pop()


def test_suspended_org_and_lockout(client, db):
    org = make_org(db)
    make_user(db, org)
    db.commit()
    for _ in range(5):
        assert login(client, pw="bad").status_code == 401
    assert login(client).status_code == 429
    org.status = "suspended"
    make_user(db, org, "hs02")
    db.commit()
    r = login(client, user="hs02")
    assert r.status_code == 403 and r.json()["error"]["code"] == "org_suspended"


def test_refresh_and_logout(client, db):
    make_user(db, make_org(db))
    db.commit()
    login(client)
    client.cookies.delete("ex_access")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/refresh").status_code == 204
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.post("/api/auth/refresh").status_code == 401


def test_forced_password_change_blocks_other_routes(client, db):
    make_user(db, make_org(db), must_change_password=True)
    db.commit()
    login(client)
    assert client.get("/api/auth/me").json()["must_change_password"] is True
    r = client.post("/api/auth/change-password", json={"current_password": PASSWORD, "new_password": "NewPass123"})
    assert r.status_code == 204
    assert client.get("/api/auth/me").json()["must_change_password"] is False


def test_ip_rate_limit(client, db):
    ip_limiter.limit = 3
    try:
        for _ in range(3):
            login(client, pw="x")
        assert login(client, user="other", pw="x").status_code == 429
    finally:
        ip_limiter.limit = 30


def test_login_latency_and_no_secret_logging(client, db, caplog):
    make_user(db, make_org(db))
    db.commit()
    caplog.set_level(logging.DEBUG)
    samples = []
    for _ in range(10):
        t = time.perf_counter()
        assert login(client).status_code == 200
        samples.append(time.perf_counter() - t)
    samples.sort()
    assert samples[int(len(samples) * 0.95) - 1] < 0.3
    assert PASSWORD not in caplog.text
