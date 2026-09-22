import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.academic.application.commands.add_members import AddMembers, AddMembersHandler
from app.modules.academic.application.commands.change_year_status import ChangeYearStatus, ChangeYearStatusHandler
from app.modules.academic.application.commands.commit_rollover import CommitRollover, CommitRolloverHandler, RolloverClass, RolloverStudent
from app.modules.academic.application.commands.create_class import CreateClass, CreateClassHandler
from app.modules.academic.application.commands.create_grade import CreateGrade, CreateGradeHandler
from app.modules.academic.application.commands.create_level import CreateLevel, CreateLevelHandler
from app.modules.academic.application.commands.create_year import CreateYear, CreateYearHandler
from app.modules.academic.application.commands.delete_class import DeleteClass, DeleteClassHandler
from app.modules.academic.application.commands.delete_grade import DeleteGrade, DeleteGradeHandler
from app.modules.academic.application.commands.delete_level import DeleteLevel, DeleteLevelHandler
from app.modules.academic.application.commands.delete_year import DeleteYear, DeleteYearHandler
from app.modules.academic.application.commands.remove_member import RemoveMember, RemoveMemberHandler
from app.modules.academic.application.commands.update_class import UpdateClass, UpdateClassHandler
from app.modules.academic.application.commands.update_grade import UpdateGrade, UpdateGradeHandler
from app.modules.academic.application.commands.update_level import UpdateLevel, UpdateLevelHandler
from app.modules.academic.application.commands.update_year import UpdateYear, UpdateYearHandler
from app.modules.academic.application.queries.get_class import GetClass, GetClassHandler
from app.modules.academic.application.queries.get_year import GetYear, GetYearHandler
from app.modules.academic.application.queries.preview_rollover import PreviewRollover, PreviewRolloverHandler
from app.modules.academic.application.queries.search_classes import SearchClasses, SearchClassesHandler
from app.modules.academic.application.queries.search_grades import SearchGrades, SearchGradesHandler
from app.modules.academic.application.queries.search_levels import SearchLevels, SearchLevelsHandler
from app.modules.academic.application.queries.search_years import SearchYears, SearchYearsHandler
from app.modules.academic.application.queries.structure_tree import StructureTree, StructureTreeHandler
from app.modules.academic.application.queries.student_record import StudentRecord, StudentRecordHandler
from app.modules.academic.interface import deps
from app.modules.academic.interface.schemas import (
    ClassCreate, ClassDetail, ClassOut, ClassSearchBody, ClassUpdate, CommitIn, GradeIn, GradeOut, GradeSearchBody, GradeUpdate, LevelIn,
    LevelOut, LevelUpdate, MemberOut, MembersIn, PreviewIn, StructureOut, YearIn, YearOut, YearUpdate, year_out,
)
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut, SearchBody

router = APIRouter(tags=["academic"])


def _page(page, out) -> PageOut:
    return PageOut(data=[out(v) for v in page.data], total=page.total, page=page.page, limit=page.limit)


def _terms(terms) -> list[dict] | None:
    return [t.model_dump() for t in terms] if terms else None


# ------------------------------------------------------------------ school years


@router.post("/school-years/search", response_model=PageOut[YearOut])
def search_years(body: SearchBody, actor: Actor = Depends(staff_actor), handle: SearchYearsHandler = Depends(deps.search_years)):
    """Filters: code, name (text) · status (enum) · start_date (day); sort also by class_count."""
    return _page(handle(actor, SearchYears(body.to_request())), year_out)


@router.post("/school-years", response_model=YearOut, status_code=201)
def create_year(body: YearIn, actor: Actor = Depends(staff_actor), handle: CreateYearHandler = Depends(deps.create_year)):
    return year_out(handle(actor, CreateYear(body.code, body.name, body.start_date, body.end_date, _terms(body.terms))))


@router.get("/school-years/{year_id}", response_model=YearOut)
def get_year(year_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: GetYearHandler = Depends(deps.get_year)):
    return year_out(handle(actor, GetYear(year_id)))


@router.patch("/school-years/{year_id}", response_model=YearOut)
def update_year(year_id: uuid.UUID, body: YearUpdate, actor: Actor = Depends(staff_actor), handle: UpdateYearHandler = Depends(deps.update_year)):
    return year_out(handle(actor, UpdateYear(year_id, body.name, body.start_date, body.end_date, _terms(body.terms))))


def _status_route(path: str, status: str):
    @router.post(f"/school-years/{{year_id}}/{path}", response_model=YearOut, name=f"{path}_year")
    def change(year_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ChangeYearStatusHandler = Depends(deps.change_year_status)):
        return year_out(handle(actor, ChangeYearStatus(year_id, status)))


for _path, _status in (("activate", "active"), ("close", "closed"), ("reopen", "planning")):
    _status_route(_path, _status)


@router.delete("/school-years/{year_id}", status_code=204)
def delete_year(year_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteYearHandler = Depends(deps.delete_year)):
    handle(actor, DeleteYear(year_id))
    return Response(status_code=204)


@router.post("/school-years/{year_id}/rollover/preview")
def rollover_preview(year_id: uuid.UUID, body: PreviewIn, actor: Actor = Depends(staff_actor),
                     handle: PreviewRolloverHandler = Depends(deps.preview_rollover)):
    """Proposed class mapping (10A1 → 11A1, top grade → tốt nghiệp) with a default action per student."""
    return handle(actor, PreviewRollover(year_id, body.target_code))


@router.post("/school-years/{year_id}/rollover/commit")
def rollover_commit(year_id: uuid.UUID, body: CommitIn, actor: Actor = Depends(staff_actor),
                    handle: CommitRolloverHandler = Depends(deps.commit_rollover)):
    classes = [RolloverClass(c.source_class_id, c.target_name, [RolloverStudent(s.user_id, s.action) for s in c.students]) for c in body.classes]
    return handle(actor, CommitRollover(year_id, body.target_code, classes, body.activate_target))


# ------------------------------------------------------------------ classes


def _class(v) -> ClassOut:
    return ClassOut(**vars(v))


@router.post("/classes/search", response_model=PageOut[ClassOut])
def search_classes(body: ClassSearchBody, actor: Actor = Depends(staff_actor), handle: SearchClassesHandler = Depends(deps.search_classes)):
    """Filters: name (text) · grade (number) · grade_id, school_year_id (uuid) · school_year (enum) · created_at (date);
    sort also by member_count."""
    return _page(handle(actor, SearchClasses(body.to_request(), body.school_year_id, body.grade_id)), _class)


@router.post("/classes", response_model=ClassOut, status_code=201)
def create_class(body: ClassCreate, actor: Actor = Depends(staff_actor), handle: CreateClassHandler = Depends(deps.create_class)):
    return _class(handle(actor, CreateClass(body.name, body.school_year, body.grade, body.grade_id, body.school_year_id)))


@router.get("/classes/{class_id}", response_model=ClassDetail)
def get_class(class_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: GetClassHandler = Depends(deps.get_class)):
    d = handle(actor, GetClass(class_id))
    return ClassDetail(**vars(d.klass), members=[MemberOut(**vars(m)) for m in d.members])


@router.patch("/classes/{class_id}", response_model=ClassOut)
def update_class(class_id: uuid.UUID, body: ClassUpdate, actor: Actor = Depends(staff_actor), handle: UpdateClassHandler = Depends(deps.update_class)):
    return _class(handle(actor, UpdateClass(class_id, body.name, body.school_year, body.grade, body.grade_id, body.school_year_id)))


@router.delete("/classes/{class_id}", status_code=204)
def delete_class(class_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteClassHandler = Depends(deps.delete_class)):
    handle(actor, DeleteClass(class_id))
    return Response(status_code=204)


@router.post("/classes/{class_id}/members", status_code=204)
def add_members(class_id: uuid.UUID, body: MembersIn, actor: Actor = Depends(staff_actor), handle: AddMembersHandler = Depends(deps.add_members)):
    handle(actor, AddMembers(class_id, body.user_ids))
    return Response(status_code=204)


@router.delete("/classes/{class_id}/members/{user_id}", status_code=204)
def remove_member(class_id: uuid.UUID, user_id: uuid.UUID, actor: Actor = Depends(staff_actor),
                  handle: RemoveMemberHandler = Depends(deps.remove_member)):
    handle(actor, RemoveMember(class_id, user_id))
    return Response(status_code=204)


# ------------------------------------------------------------------ structure


@router.get("/structure", response_model=StructureOut)
def get_structure(school_year: str | None = None, school_year_id: uuid.UUID | None = None, actor: Actor = Depends(staff_actor),
                  handle: StructureTreeHandler = Depends(deps.structure_tree)):
    """The Cấp học › Khối › Lớp tree (not a paged list)."""
    return handle(actor, StructureTree(school_year, school_year_id))


@router.post("/school-levels/search", response_model=PageOut[LevelOut])
def search_levels(body: SearchBody, actor: Actor = Depends(staff_actor), handle: SearchLevelsHandler = Depends(deps.search_levels)):
    """Filters: code, name (text) · sort (number); sort also by grade_count."""
    return _page(handle(actor, SearchLevels(body.to_request())), lambda v: LevelOut(**vars(v)))


@router.post("/school-levels", response_model=LevelOut, status_code=201)
def create_level(body: LevelIn, actor: Actor = Depends(staff_actor), handle: CreateLevelHandler = Depends(deps.create_level)):
    return LevelOut(**vars(handle(actor, CreateLevel(body.code, body.name, body.grade_from, body.grade_to, body.sort))))


@router.patch("/school-levels/{level_id}", response_model=LevelOut)
def update_level(level_id: uuid.UUID, body: LevelUpdate, actor: Actor = Depends(staff_actor), handle: UpdateLevelHandler = Depends(deps.update_level)):
    return LevelOut(**vars(handle(actor, UpdateLevel(level_id, **body.model_dump()))))


@router.delete("/school-levels/{level_id}", status_code=204)
def delete_level(level_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteLevelHandler = Depends(deps.delete_level)):
    handle(actor, DeleteLevel(level_id))
    return Response(status_code=204)


@router.post("/grades/search", response_model=PageOut[GradeOut])
def search_grades(body: GradeSearchBody, actor: Actor = Depends(staff_actor), handle: SearchGradesHandler = Depends(deps.search_grades)):
    """Filters: level (number) · name (text) · school_level_id (uuid); sort also by class_count."""
    return _page(handle(actor, SearchGrades(body.to_request(), body.school_level_id)), lambda v: GradeOut(**vars(v)))


@router.post("/grades", response_model=GradeOut, status_code=201)
def create_grade(body: GradeIn, actor: Actor = Depends(staff_actor), handle: CreateGradeHandler = Depends(deps.create_grade)):
    return GradeOut(**vars(handle(actor, CreateGrade(body.level, body.school_level_id, body.name))))


@router.patch("/grades/{grade_id}", response_model=GradeOut)
def update_grade(grade_id: uuid.UUID, body: GradeUpdate, actor: Actor = Depends(staff_actor), handle: UpdateGradeHandler = Depends(deps.update_grade)):
    return GradeOut(**vars(handle(actor, UpdateGrade(grade_id, body.level, body.name, body.school_level_id))))


@router.delete("/grades/{grade_id}", status_code=204)
def delete_grade(grade_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteGradeHandler = Depends(deps.delete_grade)):
    handle(actor, DeleteGrade(grade_id))
    return Response(status_code=204)


# ------------------------------------------------------------------ students


@router.get("/students/{student_id}/record")
def student_record(student_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: StudentRecordHandler = Depends(deps.student_record)):
    """Hồ sơ học sinh: classes per year with enrollment status, results per year, term and top-level topic."""
    return handle(actor, StudentRecord(student_id))
