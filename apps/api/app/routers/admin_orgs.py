import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import require_role
from app.models import Organization, User
from app.schemas.common import Page
from app.schemas.orgs import AdminCredential, OrgCreate, OrgCreated, OrgOut, OrgUpdate
from app.services import orgs
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/admin/orgs", tags=["admin"])
SuperAdmin = Depends(require_role("super_admin"))


def _out(org: Organization, count: int = 0) -> OrgOut:
    return OrgOut(id=org.id, code=org.code, name=org.name, status=org.status, is_system=org.is_system,
                  user_count=count, created_at=org.created_at, deleted_at=org.deleted_at)


@router.get("", response_model=Page[OrgOut])
def list_orgs(include_deleted: bool = False, params: ListParams = Depends(list_params), _: User = SuperAdmin, db: Session = Depends(get_db)):
    """Column filters: code, name (text) · status (exact) · created_at (date)."""
    items, total = orgs.list_orgs(db, params, include_deleted)
    counts = orgs.user_counts(db, [o.id for o in items])
    return Page(items=[_out(o, counts.get(o.id, 0)) for o in items], total=total, page=params.page, page_size=params.page_size)


@router.post("", response_model=OrgCreated, status_code=201)
def create_org(body: OrgCreate, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    org, admin, password = orgs.create_org(db, actor, body.code, body.name, body.admin_username, body.admin_full_name)
    db.refresh(org)
    return OrgCreated(org=_out(org, 1), admin=AdminCredential(username=admin.username, temp_password=password))


@router.get("/{org_id}", response_model=OrgOut)
def get_org(org_id: uuid.UUID, _: User = SuperAdmin, db: Session = Depends(get_db)):
    org = orgs._get(db, org_id)
    return _out(org, orgs.user_counts(db, [org.id]).get(org.id, 0))


@router.patch("/{org_id}", response_model=OrgOut)
def update_org(org_id: uuid.UUID, body: OrgUpdate, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    org = orgs.update_org(db, actor, org_id, body.code, body.name)
    return _out(org, orgs.user_counts(db, [org.id]).get(org.id, 0))


@router.post("/{org_id}/suspend", response_model=OrgOut)
def suspend(org_id: uuid.UUID, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    return _out(orgs.set_status(db, actor, org_id, "suspended"))


@router.post("/{org_id}/activate", response_model=OrgOut)
def activate(org_id: uuid.UUID, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    return _out(orgs.set_status(db, actor, org_id, "active"))


@router.delete("/{org_id}", status_code=204)
def delete_org(org_id: uuid.UUID, hard: bool = False, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    orgs.delete_org(db, actor, org_id, hard)
    return Response(status_code=204)
