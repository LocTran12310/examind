import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden
from app.deps import OrgScope, org_scope
from app.schemas.ai_models import AiModelIn, AiModelOut, AiModelUpdate, DiscoverIn, TestResult
from app.core.config import get_settings
from app.ingestion import llm
from app.services import ai_models

router = APIRouter(prefix="/ai-models", tags=["ai-models"])


def model_scope(scope: OrgScope = Depends(org_scope)) -> OrgScope:
    if scope.role not in ("org_admin", "teacher", "super_admin"):
        raise forbidden()
    return scope


def _out(scope: OrgScope, m) -> AiModelOut:
    return AiModelOut(id=m.id, name=m.name, provider=m.provider, model=m.model, base_url=m.base_url, capabilities=list(m.capabilities or []),
                      is_free=m.is_free, enabled=m.enabled, system=m.organization_id is None, has_key=bool(m.api_key_enc),
                      editable=ai_models.editable(scope, m))


@router.get("", response_model=list[AiModelOut])
def list_models(enabled: bool = False, scope: OrgScope = Depends(model_scope), db: Session = Depends(get_db)):
    return [_out(scope, m) for m in ai_models.visible(db, scope, enabled_only=enabled)]


@router.post("", response_model=AiModelOut, status_code=201)
def create_model(body: AiModelIn, scope: OrgScope = Depends(model_scope), db: Session = Depends(get_db)):
    return _out(scope, ai_models.create(db, scope, body.name, body.provider, body.model, body.base_url, body.api_key,
                                        body.capabilities, body.is_free, body.enabled))


@router.patch("/{model_id}", response_model=AiModelOut)
def update_model(model_id: uuid.UUID, body: AiModelUpdate, scope: OrgScope = Depends(model_scope), db: Session = Depends(get_db)):
    return _out(scope, ai_models.update(db, scope, model_id, **body.model_dump()))


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: uuid.UUID, scope: OrgScope = Depends(model_scope), db: Session = Depends(get_db)):
    ai_models.delete(db, scope, model_id)
    return Response(status_code=204)


@router.post("/discover")
def discover(body: DiscoverIn, scope: OrgScope = Depends(model_scope)):
    if scope.role not in ("org_admin", "super_admin"):
        raise forbidden()
    base = (body.base_url or get_settings().ollama_url).rstrip("/")
    try:
        return {"base_url": base, "models": llm.discover_ollama(base)}
    except llm.LlmError as exc:
        return {"base_url": base, "models": [], "error": str(exc)}


@router.post("/{model_id}/test", response_model=TestResult)
def test_model(model_id: uuid.UUID, scope: OrgScope = Depends(model_scope), db: Session = Depends(get_db)):
    return TestResult(**llm.test(ai_models.get_visible(db, scope, model_id)))
