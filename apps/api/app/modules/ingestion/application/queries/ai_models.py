from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.ai_access import is_super, load_visible, may_manage_models, may_see_models, model_view
from app.modules.ingestion.application.dto import AiModelView
from app.modules.ingestion.application.ports import AiModelReader
from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.ports import AiModelRepository, ChatModels
from app.modules.ingestion.domain.services.ai_parse import parse_json
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchAiModels:
    request: SearchRequest


class SearchAiModelsHandler:
    def __init__(self, reader: AiModelReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchAiModels) -> Page[AiModelView]:
        may_see_models(actor)
        page = self.reader.search(None if is_super(actor) else actor.org_id, query.request)
        return Page([model_view(actor, m) for m in page.data], page.total, page.page, page.limit)


@dataclass(frozen=True)
class DiscoverModels:
    base_url: str | None = None


class DiscoverModelsHandler:
    """Models an Ollama instance serves (the default instance when no URL is given)."""

    def __init__(self, chat: ChatModels, default_url: str):
        self.chat, self.default_url = chat, default_url

    def __call__(self, actor: Actor, query: DiscoverModels) -> dict:
        may_see_models(actor)
        may_manage_models(actor)
        base = (query.base_url or self.default_url).rstrip("/")
        try:
            return {"base_url": base, "models": self.chat.discover(base)}
        except LlmError as exc:
            return {"base_url": base, "models": [], "error": str(exc)}


def probe(chat: ChatModels, m: AiModel) -> dict:
    try:
        r = chat.chat(m, "Bạn là trợ lý kiểm tra kết nối.", 'Trả lời đúng JSON: {"ok": true}', timeout=60)
        parse_json(r.text)
        return {"ok": True, "latency_ms": r.latency_ms, "sample": r.text[:120]}
    except LlmError as exc:
        return {"ok": False, "error": str(exc)}


@dataclass(frozen=True)
class TestAiModel:
    model_id: uuid.UUID


class TestAiModelHandler:
    """A one-line JSON round trip: reachable, key valid, answers JSON."""

    def __init__(self, models: AiModelRepository, chat: ChatModels):
        self.models, self.chat = models, chat

    def __call__(self, actor: Actor, query: TestAiModel) -> dict:
        may_see_models(actor)
        return probe(self.chat, load_visible(self.models, actor, query.model_id))
