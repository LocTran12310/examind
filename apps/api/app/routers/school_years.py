import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope
from app.routers.users import staff_scope
from app.schemas.common import Page
from app.schemas.school_years import YearIn, YearOut, YearUpdate, year_out
from pydantic import BaseModel

from app.services import rollover, school_years
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/school-years", tags=["school-years"])


@router.get("", response_model=Page[YearOut])
def list_years(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: code, name (text) · status (exact) · start_date (date)."""
    rows, total = school_years.list_years(db, scope, params)
    return Page(items=[year_out(y, n) for y, n in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("", response_model=YearOut, status_code=201)
def create_year(body: YearIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    y = school_years.create_year(db, scope, body.code, body.name, body.start_date, body.end_date,
                                 [t.model_dump() for t in body.terms] if body.terms else None)
    return year_out(y)


@router.get("/{year_id}", response_model=YearOut)
def get_year(year_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return year_out(school_years.get_year(db, scope, year_id))


@router.patch("/{year_id}", response_model=YearOut)
def update_year(year_id: uuid.UUID, body: YearUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    y = school_years.update_year(db, scope, year_id, body.name, body.start_date, body.end_date,
                                 [t.model_dump() for t in body.terms] if body.terms else None)
    return year_out(y)


@router.post("/{year_id}/activate", response_model=YearOut)
def activate(year_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return year_out(school_years.set_status(db, scope, year_id, "active"))


@router.post("/{year_id}/close", response_model=YearOut)
def close(year_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return year_out(school_years.set_status(db, scope, year_id, "closed"))


@router.post("/{year_id}/reopen", response_model=YearOut)
def reopen(year_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return year_out(school_years.set_status(db, scope, year_id, "planning"))


@router.delete("/{year_id}", status_code=204)
def delete_year(year_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    school_years.delete_year(db, scope, year_id)
    return Response(status_code=204)


class PreviewIn(BaseModel):
    target_code: str | None = None


class RolloverStudent(BaseModel):
    user_id: uuid.UUID
    action: str


class RolloverClass(BaseModel):
    source_class_id: uuid.UUID
    target_name: str | None = None
    students: list[RolloverStudent] = []


class CommitIn(BaseModel):
    target_code: str
    classes: list[RolloverClass]
    activate_target: bool = False


@router.post("/{year_id}/rollover/preview")
def rollover_preview(year_id: uuid.UUID, body: PreviewIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Proposed class mapping (10A1 → 11A1, top grade → tốt nghiệp) with a default action per student."""
    return rollover.preview(db, scope, year_id, body.target_code)


@router.post("/{year_id}/rollover/commit")
def rollover_commit(year_id: uuid.UUID, body: CommitIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return rollover.commit(db, scope, year_id, body.target_code, [c.model_dump() for c in body.classes], body.activate_target)
