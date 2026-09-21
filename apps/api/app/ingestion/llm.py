"""Thin chat adapters for the providers in the model registry (exam-ingestion ADR-03).

Three wire protocols cover the free and paid options we care about:
- `ollama`    — native /api/chat (local models, JSON mode via `format: json`)
- `openai`    — any OpenAI-compatible /chat/completions (OpenAI, LM Studio, vLLM, Gemini's OpenAI endpoint)
- `anthropic` — /v1/messages
"""
import base64
from dataclasses import dataclass
import json
import re
import time

import httpx

from app.core import crypto
from app.core.config import get_settings
from app.models import AiModel

TRANSPORT: httpx.BaseTransport | None = None  # tests inject an httpx.MockTransport


class LlmError(Exception):
    pass


@dataclass
class ChatResult:
    text: str
    latency_ms: int
    model: str


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(timeout=timeout, transport=TRANSPORT) if TRANSPORT else httpx.Client(timeout=timeout)


MAX_OUTPUT_TOKENS = 1500  # bounds runaway generations (small local models in JSON mode can loop on whitespace)


def chat(m: AiModel, system: str, user: str, images: list[bytes] | None = None, json_mode: bool = True,
         timeout: float | None = None, schema: dict | None = None) -> ChatResult:
    timeout = timeout or get_settings().llm_timeout_seconds
    key = crypto.decrypt(m.api_key_enc) if m.api_key_enc else None
    t0 = time.monotonic()
    try:
        with _client(timeout) as c:
            if m.provider == "ollama":
                text = _ollama(c, m, system, user, images, json_mode, schema)
            elif m.provider == "openai":
                text = _openai(c, m, key, system, user, images, json_mode)
            elif m.provider == "anthropic":
                text = _anthropic(c, m, key, system, user, images)
            else:
                raise LlmError(f"Nhà cung cấp không hỗ trợ: {m.provider}")
    except httpx.TimeoutException as exc:
        raise LlmError("Model không phản hồi kịp (timeout)") from exc
    except httpx.HTTPError as exc:
        raise LlmError(f"Không kết nối được model: {type(exc).__name__}") from exc
    return ChatResult(text=text, latency_ms=int((time.monotonic() - t0) * 1000), model=m.model)


def _check(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        try:
            detail = r.json()
            msg = detail.get("error", {}).get("message") if isinstance(detail.get("error"), dict) else detail.get("error")
        except ValueError:
            msg = r.text[:200]
        raise LlmError(f"HTTP {r.status_code}: {msg or 'lỗi từ nhà cung cấp'}")
    return r.json()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _ollama(c, m, system, user, images, json_mode, schema=None) -> str:
    msg = {"role": "user", "content": user}
    if images:
        msg["images"] = [_b64(i) for i in images]
    body = {"model": m.model, "stream": False, "options": {"temperature": 0, "num_predict": MAX_OUTPUT_TOKENS},
            "messages": [{"role": "system", "content": system}, msg]}
    if json_mode:
        body["format"] = schema or "json"  # Ollama ≥ 0.5 accepts a JSON schema (structured outputs)
    return _check(c.post(f"{m.base_url}/api/chat", json=body))["message"]["content"]


def _openai(c, m, key, system, user, images, json_mode) -> str:
    content: list | str = user
    if images:
        content = [{"type": "text", "text": user}] + [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(i)}"}} for i in images]
    body = {"model": m.model, "temperature": 0, "max_tokens": MAX_OUTPUT_TOKENS,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    return _check(c.post(f"{m.base_url}/chat/completions", json=body, headers=headers))["choices"][0]["message"]["content"]


def _anthropic(c, m, key, system, user, images) -> str:
    content: list = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": _b64(i)}} for i in images or []]
    content.append({"type": "text", "text": user})
    body = {"model": m.model, "max_tokens": MAX_OUTPUT_TOKENS, "temperature": 0, "system": system, "messages": [{"role": "user", "content": content}]}
    headers = {"x-api-key": key or "", "anthropic-version": "2023-06-01"}
    data = _check(c.post(f"{m.base_url}/v1/messages", json=body, headers=headers))
    return "".join(part.get("text", "") for part in data.get("content", []))


def parse_json(text: str) -> dict:
    """Models wrap JSON in prose or code fences; take the outermost object."""
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        raise LlmError("Model không trả về JSON")
    try:
        value = json.loads(t[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LlmError("JSON từ model không hợp lệ") from exc
    if not isinstance(value, dict):
        raise LlmError("JSON từ model không phải object")
    return value


def discover_ollama(base_url: str) -> list[dict]:
    try:
        with _client(10) as c:
            data = _check(c.get(f"{base_url.rstrip('/')}/api/tags"))
    except httpx.HTTPError as exc:
        raise LlmError(f"Không kết nối được Ollama tại {base_url}") from exc
    out = []
    for m in data.get("models", []):
        details = m.get("details") or {}
        families = [f.lower() for f in (details.get("families") or [details.get("family") or ""])]
        vision = any(f in ("clip", "mllama", "qwen25vl", "gemma3") for f in families) or "vl" in m["name"].lower() or "vision" in m["name"].lower()
        out.append({"model": m["name"], "size": m.get("size"), "parameter_size": details.get("parameter_size"),
                    "capabilities": ["text", "vision"] if vision else ["text"]})
    return out


def test(m: AiModel) -> dict:
    try:
        r = chat(m, "Bạn là trợ lý kiểm tra kết nối.", 'Trả lời đúng JSON: {"ok": true}', timeout=60)
        parse_json(r.text)
        return {"ok": True, "latency_ms": r.latency_ms, "sample": r.text[:120]}
    except LlmError as exc:
        return {"ok": False, "error": str(exc)}
