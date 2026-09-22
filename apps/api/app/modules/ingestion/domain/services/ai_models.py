"""The AI model registry's rules (US-04, A-10, A-11)."""
import re

from app.modules.ingestion.domain.entities import CAPABILITIES, PROVIDERS
from app.shared.domain.errors import Invalid

DEFAULT_URLS = {"ollama": "http://ollama:11434", "openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com"}


def check(provider: str, model: str, base_url: str | None, capabilities: list[str], name: str) -> None:
    if provider not in PROVIDERS:
        raise Invalid("Nhà cung cấp không hợp lệ", "provider")
    if not (model or "").strip():
        raise Invalid("Nhập tên model", "model")
    if not (name or "").strip():
        raise Invalid("Nhập tên hiển thị", "name")
    if base_url and not re.match(r"^https?://", base_url):
        raise Invalid("URL phải bắt đầu bằng http:// hoặc https://", "base_url")
    if not capabilities or any(c not in CAPABILITIES for c in capabilities):
        raise Invalid("Khả năng không hợp lệ", "capabilities")
