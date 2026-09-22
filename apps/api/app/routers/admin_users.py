import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import not_found
from app.deps import require_role
from app.models import Organization, OrganizationMember, User
from app.schemas.admin import AccountOut, MembershipIn, MembershipOut, MembershipPatch, membership_out
from app.schemas.common import Page
from app.services import membership
from app.services.paging import Col, ListParams, list_params, paginate

router = APIRouter(prefix="/admin/users", tags=["admin"])
SuperAdmin = Depends(require_role("super_admin"))

ORG_COUNT = (select(func.count()).where(OrganizationMember.user_id == User.id, OrganizationMember.is_active.is_(True))
             .correlate(User).scalar_subquery())
COLS = {"username": Col(User.username), "full_name": Col(User.full_name), "home_org_code": Col(Organization.code),
        "is_active": Col(User.is_active, "bool"), "org_count": Col(ORG_COUNT, filterable=False)}


def _user(db: Session, user_id) -> User:
    u = db.get(User, user_id)
    if u is None or u.role == "super_admin":
        raise not_found("Không tìm thấy tài khoản")
    return u


@router.get("", response_model=Page[AccountOut])
def accounts(params: ListParams = Depends(list_params), _: User = SuperAdmin, db: Session = Depends(get_db)):
    """Every account of every org (school-years AC-14). Column filters: username, full_name, home_org_code (text)."""
    stmt = (select(User, Organization, ORG_COUNT).join(Organization, Organization.id == User.organization_id)
            .where(Organization.is_system.is_(False)))
    rows, total = paginate(db, stmt, params, COLS, search=[User.username, User.full_name, Organization.code], scalars=False,
                           default_sort=[User.full_name, User.id])
    items = [AccountOut(id=u.id, username=u.username, full_name=u.full_name, home_org_code=o.code, home_org_name=o.name,
                        is_active=u.is_active, org_count=n or 0) for u, o, n in rows]
    return Page(items=items, total=total, page=params.page, page_size=params.page_size)


@router.get("/{user_id}/memberships", response_model=Page[MembershipOut])
def memberships(user_id: uuid.UUID, params: ListParams = Depends(list_params), _: User = SuperAdmin, db: Session = Depends(get_db)):
    """User → orgs, home org first."""
    user = _user(db, user_id)
    stmt = (select(OrganizationMember, Organization).join(Organization, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user.id))
    cols = {"org_code": Col(Organization.code), "org_name": Col(Organization.name), "role": Col(OrganizationMember.role, "exact")}
    rows, total = paginate(db, stmt, params, cols, scalars=False, default_sort=[(Organization.id != user.organization_id), Organization.name])
    return Page(items=[membership_out(m, user, o) for m, o in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("/{user_id}/memberships", response_model=MembershipOut, status_code=201)
def add_membership(user_id: uuid.UUID, body: MembershipIn, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    user = _user(db, user_id)
    m = membership.add(db, actor, body.org_id, user, body.role)
    return membership_out(m, user, db.get(Organization, body.org_id))


@router.patch("/{user_id}/memberships/{org_id}", response_model=MembershipOut)
def update_membership(user_id: uuid.UUID, org_id: uuid.UUID, body: MembershipPatch, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    user = _user(db, user_id)
    m = membership.update(db, actor, org_id, user.id, body.role, body.is_active)
    return membership_out(m, user, db.get(Organization, org_id))


@router.delete("/{user_id}/memberships/{org_id}", status_code=204)
def remove_membership(user_id: uuid.UUID, org_id: uuid.UUID, actor: User = SuperAdmin, db: Session = Depends(get_db)):
    membership.remove(db, actor, org_id, _user(db, user_id).id)
    return Response(status_code=204)
