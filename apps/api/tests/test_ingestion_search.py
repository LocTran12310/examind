"""Documents and AI models moved to `POST …/search` (architecture-refactor UOW-05, ADR-03)."""
import pytest
from cryptography.fernet import Fernet

from app.shared.infrastructure.config import get_settings
from tests.factories import login_as
from tests.test_documents_api import sample, teacher_with_taxonomy, upload


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


def test_document_search_filters_sort_and_page(client, db):
    teacher_with_taxonomy(client, db)
    upload(client, "de-kho.docx", sample("de-kho.docx"), {"source_name": "THPT Chu Văn An"})
    upload(client, "toan10.docx", sample("de-mau-toan10.docx"))
    upload(client, "thpt.pdf", sample("de-mau-toan10.pdf"))
    body = client.post("/api/documents/search", json={}).json()
    assert set(body) == {"data", "total", "page", "limit"} and body["total"] == 3
    assert [d["filename"] for d in body["data"]] == ["thpt.pdf", "toan10.docx", "de-kho.docx"]  # newest first
    only_pdf = client.post("/api/documents/search", json={"filters": {"mime": {"value": ["application/pdf"]}}}).json()
    assert [d["filename"] for d in only_pdf["data"]] == ["thpt.pdf"]
    by_source = client.post("/api/documents/search", json={"q": "chu van"}).json()
    assert [d["filename"] for d in by_source["data"]] == ["de-kho.docx"]
    assert client.post("/api/documents/search", json={"filters": {"filename": {"operator": "+", "value": "toan"}}}).json()["total"] == 1
    assert client.post("/api/documents/search", json={"filters": {"status": {"value": "queued"}}, "limit": 2}).json()["total"] == 3
    named = client.post("/api/documents/search", json={"sort": [{"field": "filename", "desc": False}], "limit": 2, "page": 2}).json()
    assert [d["filename"] for d in named["data"]] == ["toan10.docx"] and named["page"] == 2
    r = client.post("/api/documents/search", json={"filters": {"storage_key": {"value": "x"}}})
    assert r.status_code == 422 and r.json()["code"] == "bad_filter"
    assert client.post("/api/documents/search", json={"sort": [{"field": "nope"}]}).json()["code"] == "bad_sort"
    assert client.get("/api/documents").status_code == 405


def test_ai_model_search(client, db):
    login_as(client, db, "org_admin")
    for name, provider in (("Qwen", "ollama"), ("GPT", "openai"), ("Claude", "anthropic")):
        client.post("/api/ai-models", json={"name": name, "provider": provider, "model": name.lower(), "api_key": "k" if provider != "ollama" else None,
                                            "is_free": provider == "ollama"})
    body = client.post("/api/ai-models/search", json={}).json()
    assert [m["name"] for m in body["data"]] == ["Claude", "GPT", "Qwen"] and body["total"] == 3
    free = client.post("/api/ai-models/search", json={"filters": {"is_free": {"value": "true"}}}).json()
    assert [m["name"] for m in free["data"]] == ["Qwen"]
    assert client.post("/api/ai-models/search", json={"filters": {"provider": {"value": ["openai", "anthropic"]}}}).json()["total"] == 2
    assert client.post("/api/ai-models/search", json={"q": "gp"}).json()["data"][0]["name"] == "GPT"
    assert client.post("/api/ai-models/search", json={"filters": {"api_key_enc": {"value": "x"}}}).status_code == 422
    assert client.get("/api/ai-models").status_code == 405
