from cryptography.fernet import Fernet
import pytest

from app.modules.ingestion.domain.entities import AiModel
from app.shared.infrastructure.config import get_settings
from tests.factories import login_as, make_org, make_user


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


OLLAMA = {"name": "Qwen 7B", "provider": "ollama", "model": "qwen2.5:7b", "base_url": "http://ollama:11434", "capabilities": ["text"]}


def test_org_admin_crud_and_key_never_returned(client, db):
    login_as(client, db, "org_admin")
    r = client.post("/api/ai-models", json=OLLAMA)
    assert r.status_code == 201, r.text
    m = r.json()
    assert m["is_free"] and not m["system"] and m["editable"] and not m["has_key"]
    paid = client.post("/api/ai-models", json={"name": "GPT", "provider": "openai", "model": "gpt-4o-mini", "api_key": "sk-secret", "is_free": False}).json()
    assert paid["has_key"] and "api_key" not in paid and "sk-secret" not in str(paid)
    assert paid["base_url"] == "https://api.openai.com/v1"
    stored = db.get(AiModel, paid["id"])
    assert stored.api_key_enc and "sk-secret" not in stored.api_key_enc
    r = client.patch(f"/api/ai-models/{m['id']}", json={"enabled": False, "name": "Qwen tắt"})
    assert r.json()["enabled"] is False and r.json()["name"] == "Qwen tắt"
    assert [x["name"] for x in client.post("/api/ai-models/search", json={"filters": {"enabled": {"value": True}}}).json()["data"]] == ["GPT"]
    assert client.patch(f"/api/ai-models/{paid['id']}", json={"api_key": ""}).json()["has_key"] is False
    assert client.delete(f"/api/ai-models/{m['id']}").status_code == 204
    assert client.post("/api/ai-models", json={**OLLAMA, "provider": "bogus"}).status_code == 422


def test_system_models_visible_but_read_only(client, db):
    login_as(client, db, "super_admin")
    sys_model = client.post("/api/ai-models", json={**OLLAMA, "name": "Hệ thống Qwen"}).json()
    assert sys_model["system"] is True
    client.cookies.clear()
    org = make_org(db, "orgx")
    login_as(client, db, "org_admin", org=org)
    listed = {m["name"]: m for m in client.post("/api/ai-models/search", json={}).json()["data"]}
    assert listed["Hệ thống Qwen"]["system"] and not listed["Hệ thống Qwen"]["editable"]
    assert client.patch(f"/api/ai-models/{sys_model['id']}", json={"name": "x"}).status_code == 403
    assert client.delete(f"/api/ai-models/{sys_model['id']}").status_code == 403


def test_isolation_and_teacher_read_only(client, db):
    admin = login_as(client, db, "org_admin")
    mine = client.post("/api/ai-models", json=OLLAMA).json()
    other = client.__class__(client.app)
    org_b = make_org(db, "orgb")
    make_user(db, org_b, "adminb", role="org_admin")
    db.commit()
    other.post("/api/auth/login", json={"org_code": "orgb", "username": "adminb", "password": "Secret123!"})
    assert other.post("/api/ai-models/search", json={}).json()["data"] == []
    assert other.patch(f"/api/ai-models/{mine['id']}", json={"name": "x"}).status_code == 404
    teacher_client = client.__class__(client.app)
    make_user(db, admin.organization, "gv", role="teacher")
    db.commit()
    teacher_client.post("/api/auth/login", json={"org_code": "trungtama", "username": "gv", "password": "Secret123!"})
    assert len(teacher_client.post("/api/ai-models/search", json={}).json()["data"]) == 1
    assert teacher_client.post("/api/ai-models", json=OLLAMA).status_code == 403


def test_missing_encryption_key(client, db, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", "")
    login_as(client, db, "org_admin")
    r = client.post("/api/ai-models", json={**OLLAMA, "api_key": "x"})
    assert r.status_code == 500 and r.json()["code"] == "encryption_unavailable"
