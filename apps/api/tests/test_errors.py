"""Error body and request id (architecture-refactor AC-03)."""
from fastapi.testclient import TestClient

from app.main import app


def test_error_body_carries_code_message_and_request_id():
    c = TestClient(app)
    r = c.get("/api/auth/me")
    body = r.json()
    assert r.status_code == 401
    assert body["code"] == "unauthenticated" and body["message"]
    assert body["details"]["requestId"] == r.headers["X-Request-Id"]


def test_validation_errors_list_fields():
    c = TestClient(app)
    r = c.post("/api/auth/login", json={})
    assert r.status_code == 422 and r.json()["code"] == "validation_error"
    assert r.json()["details"]["fields"]


def test_incoming_request_id_is_kept_when_sane():
    c = TestClient(app)
    r = c.get("/api/health", headers={"X-Request-Id": "abc-12345678"})
    assert r.headers["X-Request-Id"] == "abc-12345678"
    r = c.get("/api/health", headers={"X-Request-Id": "x"})
    assert r.headers["X-Request-Id"] != "x" and len(r.headers["X-Request-Id"]) == 32
