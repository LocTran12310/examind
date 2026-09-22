import json

import httpx
import pytest
from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.modules.ingestion.infrastructure.adapters import llm
from app.models import AiModel
from tests.factories import login_as


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_encryption_key", Fernet.generate_key().decode())


@pytest.fixture
def stub(monkeypatch):
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        body = json.loads(request.content or b"{}")
        path = request.url.path
        if path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen2.5:7b", "size": 4, "details": {"family": "qwen2", "parameter_size": "7.6B"}},
                                                        {"name": "qwen2.5vl:7b", "details": {"families": ["qwen25vl"]}}]})
        if path == "/api/chat":
            assert body["format"] and body["options"]["temperature"] == 0 and body["options"]["num_predict"] == 1500
            return httpx.Response(200, json={"message": {"content": '{"ok": true}'}})
        if path == "/v1/chat/completions":
            if request.headers.get("authorization") != "Bearer sk-1":
                return httpx.Response(401, json={"error": {"message": "bad key"}})
            return httpx.Response(200, json={"choices": [{"message": {"content": "```json\n{\"ok\": true}\n```"}}]})
        if path == "/v1/messages":
            assert request.headers["x-api-key"] == "ak-1"
            return httpx.Response(200, json={"content": [{"type": "text", "text": 'Kết quả: {"ok": true}'}]})
        if path == "/slow/api/chat":
            raise httpx.ReadTimeout("slow")
        return httpx.Response(404)

    monkeypatch.setattr(llm, "TRANSPORT", httpx.MockTransport(handler))
    return calls


def model(provider, base, key=None, name="m"):
    from app.modules.ingestion.infrastructure.adapters import crypto

    return AiModel(name=name, provider=provider, model="x", base_url=base, api_key_enc=crypto.encrypt(key) if key else None, capabilities=["text"])


def test_three_adapters(stub):
    for m in (model("ollama", "http://o"), model("openai", "http://g/v1", "sk-1"), model("anthropic", "http://a", "ak-1")):
        r = llm.chat(m, "sys", "user")
        assert llm.parse_json(r.text) == {"ok": True}
    oa = [c for c in stub if c.url.path == "/v1/chat/completions"][0]
    assert json.loads(oa.content)["response_format"] == {"type": "json_object"}


def test_images_are_sent(stub):
    llm.chat(model("ollama", "http://o"), "s", "u", images=[b"PNG"])
    body = json.loads([c for c in stub if c.url.path == "/api/chat"][0].content)
    assert body["messages"][1]["images"] == ["UE5H"]


def test_errors_are_readable(stub):
    with pytest.raises(llm.LlmError, match="HTTP 401: bad key"):
        llm.chat(model("openai", "http://g/v1", "wrong"), "s", "u")
    with pytest.raises(llm.LlmError, match="timeout"):
        llm.chat(model("ollama", "http://o/slow"), "s", "u")
    with pytest.raises(llm.LlmError):
        llm.parse_json("xin lỗi, tôi không biết")


def test_discover_and_test_endpoints(stub, client, db):
    login_as(client, db, "org_admin")
    r = client.post("/api/ai-models/discover", json={"base_url": "http://o"}).json()
    assert [m["model"] for m in r["models"]] == ["qwen2.5:7b", "qwen2.5vl:7b"]
    assert r["models"][1]["capabilities"] == ["text", "vision"]
    m = client.post("/api/ai-models", json={"name": "Q", "provider": "ollama", "model": "qwen2.5:7b", "base_url": "http://o"}).json()
    res = client.post(f"/api/ai-models/{m['id']}/test").json()
    assert res["ok"] is True and res["latency_ms"] is not None
    bad = client.post("/api/ai-models", json={"name": "S", "provider": "ollama", "model": "x", "base_url": "http://o/slow"}).json()
    res = client.post(f"/api/ai-models/{bad['id']}/test").json()
    assert res["ok"] is False and "timeout" in res["error"]
