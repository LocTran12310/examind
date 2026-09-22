import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import require_role
from app.models import Organization, OrganizationMember, User
from app.schemas.admin import MemberIn, MembershipOut, MembershipPatch, membership_out
from app.schemas.common import Page
from app.schemas.orgs import AdminCredential, OrgCreate, OrgCreated, OrgOut, OrgUpdate
from app.services import membership, orgs
from app.services.paging import Col, ListParams, list_params, paginate

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


MEMBER_COLS = {
    "username": Col(User.username),
    "full_name": Col(User.full_name),
    "role": Col(OrganizationMember.role, "exact"),
    "is_active": Col(OrganizationMember.is_active, "bool"),
}


@router.get("/{org_id}/members", response_model=Page[MembershipOut])
def org_members(org_id: uuid.UUID, params: ListParams = Depends(list_params), _: User = SuperAdmin, db: Session = Depends(get_db)):
    """Org → users (school-years AC-13)."""
    org = orgs._get(db, org_id)
    stmt = (select(OrganizationMember, User).join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == org.id))
    rows, total = paginate(db, stmt, params, MEMBER_COLS, search=[User.username, User.full_name], scalars=False,
                           default_sort=[User.full_name, User.id])
    return Page(items=[membership_out(m, u, org) for m, u in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("/{org_id}/members", response_model=MembershipOut, status_code=201)
def add_org_member(org_id: uuid.UUID, body: MemberIn, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    org = orgs._get(db, org_id)
    _, user = membership.find_account(db, body.org_code, body.username)
    return membership_out(membership.add(db, actor, org.id, user, body.role), user, org)


@router.patch("/{org_id}/members/{user_id}", response_model=MembershipOut)
def update_org_member(org_id: uuid.UUID, user_id: uuid.UUID, body: MembershipPatch, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    org = orgs._get(db, org_id)
    m = membership.update(db, actor, org.id, user_id, body.role, body.is_active)
    return membership_out(m, db.get(User, user_id), org)


@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_org_member(org_id: uuid.UUID, user_id: uuid.UUID, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    membership.remove(db, actor, orgs._get(db, org_id).id, user_id)
    return Response(status_code=204)
