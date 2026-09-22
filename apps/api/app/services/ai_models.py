"""AI model registry: org models + system-wide models (US-04, A-10, A-11)."""
import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.errors import forbidden, not_found, validation
from app.deps import OrgScope
from app.services.paging import Col, ListParams, paginate
from app.models import AiModel
from app.models.ai_model import CAPABILITIES, PROVIDERS
from app.services import audit

DEFAULT_URLS = {"ollama": "http://ollama:11434", "openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com"}


def is_super(scope: OrgScope) -> bool:
    return scope.role == "super_admin"


MODEL_COLS = {
    "name": Col(AiModel.name),
    "provider": Col(AiModel.provider, "exact"),
    "model": Col(AiModel.model),
    "enabled": Col(AiModel.enabled, "bool"),
    "is_free": Col(AiModel.is_free, "bool"),
}


def visible_stmt(scope: OrgScope):
    stmt = select(AiModel)
    if not is_super(scope):
        return stmt.where(or_(AiModel.organization_id == scope.org_id, AiModel.organization_id.is_(None)))
    return stmt.where(AiModel.organization_id.is_(None))


def list_models(db: Session, scope: OrgScope, params: ListParams):
    return paginate(db, visible_stmt(scope), params, MODEL_COLS, search=[AiModel.name, AiModel.model],
                    default_sort=[AiModel.organization_id.nulls_first(), AiModel.name, AiModel.id])


def visible(db: Session, scope: OrgScope, enabled_only: bool = False) -> list[AiModel]:
    stmt = select(AiModel)
    if not is_super(scope):
        stmt = stmt.where(or_(AiModel.organization_id == scope.org_id, AiModel.organization_id.is_(None)))
    else:
        stmt = stmt.where(AiModel.organization_id.is_(None))
    if enabled_only:
        stmt = stmt.where(AiModel.enabled.is_(True))
    return db.scalars(stmt.order_by(AiModel.organization_id.nulls_first(), AiModel.name)).all()


def get_visible(db: Session, scope: OrgScope, model_id) -> AiModel:
    m = db.get(AiModel, model_id)
    if m is None or (m.organization_id not in (None, scope.org_id)):
        raise not_found("Không tìm thấy model")
    return m


def resolve_for_org(db: Session, org_id, model_id) -> AiModel | None:
    """Model usable by an org during ingestion (worker side, no scope)."""
    try:
        m = db.get(AiModel, uuid.UUID(str(model_id)))
    except (ValueError, TypeError):
        return None
    if m is None or not m.enabled or m.organization_id not in (None, org_id):
        return None
    return m


def editable(scope: OrgScope, m: AiModel) -> bool:
    if m.organization_id is None:
        return is_super(scope)
    return scope.role == "org_admin" and m.organization_id == scope.org_id


def _check(provider: str, model: str, base_url: str | None, capabilities: list[str], name: str) -> None:
    if provider not in PROVIDERS:
        raise validation("Nhà cung cấp không hợp lệ", "provider")
    if not (model or "").strip():
        raise validation("Nhập tên model", "model")
    if not (name or "").strip():
        raise validation("Nhập tên hiển thị", "name")
    if base_url and not re.match(r"^https?://", base_url):
        raise validation("URL phải bắt đầu bằng http:// hoặc https://", "base_url")
    if not capabilities or any(c not in CAPABILITIES for c in capabilities):
        raise validation("Khả năng không hợp lệ", "capabilities")


def create(db: Session, scope: OrgScope, name: str, provider: str, model: str, base_url: str | None, api_key: str | None,
           capabilities: list[str], is_free: bool, enabled: bool = True) -> AiModel:
    if scope.role not in ("org_admin", "super_admin"):
        raise forbidden()
    _check(provider, model, base_url, capabilities, name)
    m = AiModel(organization_id=None if is_super(scope) else scope.org_id, name=name.strip(), provider=provider, model=model.strip(),
                base_url=(base_url or DEFAULT_URLS[provider]).rstrip("/"), api_key_enc=crypto.encrypt(api_key) if api_key else None,
                capabilities=capabilities, is_free=is_free, enabled=enabled)
    db.add(m)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "ai_model.create", "ai_model", m.id, provider=provider, model=m.model)
    return m


def update(db: Session, scope: OrgScope, model_id, **changes) -> AiModel:
    m = get_visible(db, scope, model_id)
    if not editable(scope, m):
        raise forbidden()
    for k in ("name", "provider", "model", "base_url", "capabilities", "is_free", "enabled"):
        if changes.get(k) is not None:
            setattr(m, k, changes[k].strip() if isinstance(changes[k], str) else changes[k])
    _check(m.provider, m.model, m.base_url, m.capabilities, m.name)
    if changes.get("api_key") is not None:
        m.api_key_enc = crypto.encrypt(changes["api_key"]) if changes["api_key"] else None
    audit.record(db, scope.user, scope.org_id, "ai_model.update", "ai_model", m.id)
    return m


def delete(db: Session, scope: OrgScope, model_id) -> None:
    m = get_visible(db, scope, model_id)
    if not editable(scope, m):
        raise forbidden()
    db.delete(m)
    audit.record(db, scope.user, scope.org_id, "ai_model.delete", "ai_model", m.id)
