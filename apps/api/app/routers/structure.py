import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope
from app.routers.users import staff_scope
from app.schemas.common import Page
from app.schemas.structure import GradeIn, GradeOut, GradeUpdate, LevelIn, LevelOut, LevelUpdate, StructureOut
from app.services import structure
from app.services.paging import ListParams, list_params

router = APIRouter(tags=["structure"])


def _level(lv, n=0) -> LevelOut:
    return LevelOut(id=lv.id, code=lv.code, name=lv.name, grade_from=lv.grade_from, grade_to=lv.grade_to, sort=lv.sort, grade_count=n or 0)


def _grade(g, n=0) -> GradeOut:
    return GradeOut(id=g.id, level=g.level, name=g.name, school_level_id=g.school_level_id, class_count=n or 0)


@router.get("/structure", response_model=StructureOut)
def get_structure(school_year: str | None = None, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return structure.tree(db, scope, school_year)


@router.get("/school-levels", response_model=Page[LevelOut])
def list_levels(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    rows, total = structure.list_levels(db, scope, params)
    return Page(items=[_level(lv, n) for lv, n in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("/school-levels", response_model=LevelOut, status_code=201)
def create_level(body: LevelIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _level(structure.create_level(db, scope, body.code, body.name, body.grade_from, body.grade_to, body.sort))


@router.patch("/school-levels/{level_id}", response_model=LevelOut)
def update_level(level_id: uuid.UUID, body: LevelUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _level(structure.update_level(db, scope, level_id, **body.model_dump()))


@router.delete("/school-levels/{level_id}", status_code=204)
def delete_level(level_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    structure.delete_level(db, scope, level_id)
    return Response(status_code=204)


@router.get("/grades", response_model=Page[GradeOut])
def list_grades(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: level (number) · name (text) · school_level_id."""
    rows, total = structure.list_grades(db, scope, params)
    return Page(items=[_grade(g, n) for g, n in rows], total=total, page=params.page, page_size=params.page_size)


@router.post("/grades", response_model=GradeOut, status_code=201)
def create_grade(body: GradeIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _grade(structure.create_grade(db, scope, body.level, body.school_level_id, body.name))


@router.patch("/grades/{grade_id}", response_model=GradeOut)
def update_grade(grade_id: uuid.UUID, body: GradeUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _grade(structure.update_grade(db, scope, grade_id, body.level, body.name, body.school_level_id))


@router.delete("/grades/{grade_id}", status_code=204)
def delete_grade(grade_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    structure.delete_grade(db, scope, grade_id)
    return Response(status_code=204)
