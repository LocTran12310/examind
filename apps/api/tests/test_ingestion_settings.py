import pytest
from cryptography.fernet import Fernet

from app.core.config import get_settings
from tests.factories import login_as, make_user
from tests.test_documents_api import sample, upload


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


def test_defaults_roundtrip_and_used_by_uploads(client, db):
    admin = login_as(client, db, "org_admin")
    assert client.get("/api/org/settings/ingestion").json()["split_mode"] == "rule"
    mid = client.post("/api/ai-models", json={"name": "q", "provider": "ollama", "model": "q", "base_url": "http://o"}).json()["id"]
    r = client.put("/api/org/settings/ingestion", json={"split_mode": "rule_ai", "split_models": [mid], "threshold": 0.9})
    assert r.status_code == 200 and r.json()["split_models"] == [mid]
    doc = upload(client, "k.docx", sample("de-kho.docx")).json()["document"]
    assert doc["processing_config"]["split_mode"] == "rule_ai" and doc["processing_config"]["threshold"] == 0.9
    doc2 = upload(client, "t.docx", sample("de-thpt2025-toan.docx"), config={"split_mode": "rule"}).json()["document"]
    assert doc2["processing_config"]["split_mode"] == "rule"
    teacher = client.__class__(client.app)
    make_user(db, admin.organization, "gv", role="teacher")
    db.commit()
    teacher.post("/api/auth/login", json={"org_code": "trungtama", "username": "gv", "password": "Secret123!"})
    assert teacher.get("/api/org/settings/ingestion").json()["split_mode"] == "rule_ai"
    assert teacher.put("/api/org/settings/ingestion", json={"split_mode": "rule"}).status_code == 403


def test_invalid_models_refused(client, db):
    login_as(client, db, "org_admin")
    import uuid

    assert client.put("/api/org/settings/ingestion", json={"split_models": [str(uuid.uuid4())]}).status_code == 422
    text_only = client.post("/api/ai-models", json={"name": "q", "provider": "ollama", "model": "q", "base_url": "http://o"}).json()["id"]
    assert client.put("/api/org/settings/ingestion", json={"vision_model": text_only}).status_code == 422
