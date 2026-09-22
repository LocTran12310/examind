import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope
from app.routers.users import staff_scope
from app.schemas.classes import ClassCreate, ClassDetail, ClassOut, ClassUpdate, MembersIn, class_out
from app.schemas.users import user_out
from app.schemas.common import Page
from app.services import classes
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=Page[ClassOut])
def list_classes(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: name (text) · grade (number, grade_min/grade_max) · school_year (exact) · created_at (date)."""
    rows, total = classes.list_classes(db, scope, params)
    return Page(items=[class_out(c, n) for c, n in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("", response_model=ClassOut, status_code=201)
def create_class(body: ClassCreate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    c = classes.create_class(db, scope, body.name, body.school_year or classes.current_school_year(), body.grade)
    db.refresh(c)
    return class_out(c)


@router.get("/{class_id}", response_model=ClassDetail)
def get_class(class_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    c = classes.get_class(db, scope, class_id)
    ms = classes.members(db, scope, class_id)
    return ClassDetail(**class_out(c, len(ms)).model_dump(), members=[user_out(u) for u in ms])


@router.patch("/{class_id}", response_model=ClassOut)
def update_class(class_id: uuid.UUID, body: ClassUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return class_out(classes.update_class(db, scope, class_id, body.name, body.school_year, body.grade))


@router.delete("/{class_id}", status_code=204)
def delete_class(class_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    classes.delete_class(db, scope, class_id)
    return Response(status_code=204)


@router.post("/{class_id}/members", status_code=204)
def add_members(class_id: uuid.UUID, body: MembersIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    classes.add_members(db, scope, class_id, body.user_ids)
    return Response(status_code=204)


@router.delete("/{class_id}/members/{user_id}", status_code=204)
def remove_member(class_id: uuid.UUID, user_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    classes.remove_member(db, scope, class_id, user_id)
    return Response(status_code=204)
