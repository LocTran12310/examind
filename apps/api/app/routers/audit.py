import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden
from app.deps import OrgScope, org_scope
from app.models import AuditLog, Organization, User
from app.schemas.common import Page
from app.schemas.school_years import AuditOut
from app.services.paging import Col, ListParams, list_params, paginate

router = APIRouter(prefix="/audit", tags=["audit"])

COLS = {"action": Col(AuditLog.action), "target_type": Col(AuditLog.target_type, "exact"), "target_id": Col(AuditLog.target_id, "uuid"),
        "created_at": Col(AuditLog.created_at, "date"), "actor_id": Col(AuditLog.actor_id, "uuid")}


@router.get("", response_model=Page[AuditOut])
def history(params: ListParams = Depends(list_params), related: uuid.UUID | None = None, scope: OrgScope = Depends(org_scope),
            db: Session = Depends(get_db)):
    """History = the audit log (school-years ADR-05). Org admins see their org; the super admin sees every org.
    `related=<id>` also matches entries whose data lists that id (e.g. class member changes for a student)."""
    if scope.role != "org_admin" and not scope.is_super:
        raise forbidden()
    stmt = (select(AuditLog, User.full_name, Organization.code).outerjoin(User, User.id == AuditLog.actor_id)
            .join(Organization, Organization.id == AuditLog.organization_id))
    if not (scope.is_super and scope.role == "super_admin"):
        stmt = stmt.where(AuditLog.organization_id == scope.org_id)
    if related:
        stmt = stmt.where(or_(AuditLog.target_id == related, AuditLog.data["user_ids"].contains([str(related)])))
    rows, total = paginate(db, stmt, params, COLS, search=[AuditLog.action], scalars=False,
                           default_sort=[AuditLog.created_at.desc(), AuditLog.id])
    items = [AuditOut(id=a.id, created_at=a.created_at, organization_id=a.organization_id, organization_code=code, actor_id=a.actor_id,
                      actor_name=name, action=a.action, target_type=a.target_type, target_id=a.target_id, data=a.data or {})
             for a, name, code in rows]
    return Page(items=items, total=total, page=params.page, page_size=params.page_size)
