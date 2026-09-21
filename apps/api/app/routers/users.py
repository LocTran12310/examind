import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden
from app.deps import STAFF, OrgScope, org_scope
from app.schemas.common import Page
from app.schemas.users import Credential, UserCreate, UserCreated, UserOut, UserUpdate, user_out
from app.services import user_import, users

router = APIRouter(prefix="/users", tags=["users"])


def staff_scope(scope: OrgScope = Depends(org_scope)) -> OrgScope:
    if scope.role not in STAFF:
        raise forbidden()
    return scope


@router.get("", response_model=Page[UserOut])
def list_users(q: str = "", role: str | None = None, class_id: uuid.UUID | None = None, active: bool | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500),
               scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    items, total = users.list_users(db, scope, q, role, class_id, active, page, page_size)
    classes = users.class_ids_by_user(db, [u.id for u in items])
    return Page(items=[user_out(u, classes.get(u.id)) for u in items], total=total, page=page, page_size=page_size)


@router.post("", response_model=UserCreated, status_code=201)
def create_user(body: UserCreate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user, temp = users.create_user(db, scope, body.full_name, body.role, body.username, body.email, body.password)
    return UserCreated(user=user_out(user), temp_password=temp)


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
    user = users.get_user(db, scope, user_id)
    if not users.can_manage(scope, user.role) and scope.role != "org_admin":
        raise forbidden()
    return user_out(user, users.class_ids_by_user(db, [user.id]).get(user.id))


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, body: UserUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user = users.update_user(db, scope, user_id, **body.model_dump())
    return user_out(user, users.class_ids_by_user(db, [user.id]).get(user.id))


@router.post("/{user_id}/reset-password", response_model=Credential)
def reset_password(user_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    user, password = users.reset_password(db, scope, user_id)
    return Credential(user_id=user.id, username=user.username, full_name=user.full_name, temp_password=password)
