import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden
from app.deps import STAFF, OrgScope, org_scope
from app.schemas.common import Page
from app.schemas.users import Credential, LinkIn, UserCreate, UserCreated, UserOut, UserUpdate, user_out
from app.services import user_import, users
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/users", tags=["users"])


def staff_scope(scope: OrgScope = Depends(org_scope)) -> OrgScope:
    if scope.role not in STAFF:
        raise forbidden()
    return scope


@router.get("", response_model=Page[UserOut])
def list_users(class_id: uuid.UUID | None = None, params: ListParams = Depends(list_params),
               scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: username, full_name, email (text) · role (exact) · is_active (bool) · created_at/last_login_at (date)."""
    rows, total = users.list_users(db, scope, params, class_id)
    classes = users.class_ids_by_user(db, [u.id for u, _ in rows], scope.org_id)
    return Page(items=[user_out(u, classes.get(u.id), m) for u, m in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("", response_model=UserCreated, status_code=201)
def create_user(body: UserCreate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user, temp = users.create_user(db, scope, body.full_name, body.role, body.username, body.email, body.password)
    return UserCreated(user=user_out(user), temp_password=temp)


@router.post("/link", response_model=UserOut, status_code=201)
def link_account(body: LinkIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Add an existing account from another organisation (A-10)."""
    from app.services import membership

    user, m = membership.link(db, scope, body.org_code, body.username, body.role)
    return user_out(user, [], m)


@router.delete("/{user_id}/membership", status_code=204)
def unlink_account(user_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    from fastapi import Response

    from app.services import membership

    membership.unlink(db, scope, user_id)
    return Response(status_code=204)


class ImportRowsIn(BaseModel):
    rows: list[dict]


@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    raw = user_import.parse_file(file.filename or "", await file.read())
    rows = [r.as_dict() for r in user_import.validate_rows(db, scope, raw)]
    errors = sum(1 for r in rows if r["errors"])
    return {"rows": rows, "valid_count": len(rows) - errors, "error_count": errors}


@router.post("/import/commit", status_code=201)
def import_commit(body: ImportRowsIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return {"created": user_import.commit(db, scope, body.rows)}


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user, m = users.get_member(db, scope, user_id)
    if not users.can_manage(scope, m.role) and scope.role != "org_admin":
        raise forbidden()
    return user_out(user, users.class_ids_by_user(db, [user.id], scope.org_id).get(user.id), m)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, body: UserUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user = users.update_user(db, scope, user_id, **body.model_dump())
    return user_out(user, users.class_ids_by_user(db, [user.id], scope.org_id).get(user.id), users.get_member(db, scope, user.id)[1])


@router.post("/{user_id}/reset-password", response_model=Credential)
def reset_password(user_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user, password = users.reset_password(db, scope, user_id)
    return Credential(user_id=user.id, username=user.username, full_name=user.full_name, temp_password=password)
