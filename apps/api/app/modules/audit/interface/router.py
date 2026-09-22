from fastapi import APIRouter, Depends

from app.modules.audit.application.queries.search_audit import SearchAudit, SearchAuditHandler
from app.modules.audit.interface import deps
from app.modules.audit.interface.schemas import AuditOut, AuditSearchBody, audit_out
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor
from app.shared.interface.search_schemas import PageOut

router = APIRouter(tags=["audit"])


@router.post("/audit/search", response_model=PageOut[AuditOut])
def search_audit(body: AuditSearchBody, actor: Actor = Depends(current_actor), handle: SearchAuditHandler = Depends(deps.search_audit)):
    """History (school-years ADR-05). Filters: action (text) · target_type (enum) · target_id, actor_id, organization_id (uuid) ·
    created_at (date); scope: target_id, organization_id, related (entries whose data lists that user). Newest first."""
    page = handle(actor, SearchAudit(body.to_request(), body.related, body.target_id, body.organization_id))
    return PageOut(data=[audit_out(r) for r in page.data], total=page.total, page=page.page, limit=page.limit)
