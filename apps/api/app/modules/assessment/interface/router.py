import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.assessment.application.commands.add_exam_questions import AddExamQuestions, AddExamQuestionsHandler
from app.modules.assessment.application.commands.apply_blueprint import ApplyBlueprint, ApplyBlueprintHandler
from app.modules.assessment.application.commands.create_assignment import CreateAssignment, CreateAssignmentHandler
from app.modules.assessment.application.commands.create_exam import CreateExam, CreateExamHandler
from app.modules.assessment.application.commands.delete_assignment import DeleteAssignment, DeleteAssignmentHandler
from app.modules.assessment.application.commands.delete_exam import DeleteExam, DeleteExamHandler
from app.modules.assessment.application.commands.grade_essay import GradeEssay, GradeEssayHandler
from app.modules.assessment.application.commands.record_tab_switch import RecordTabSwitch, RecordTabSwitchHandler
from app.modules.assessment.application.commands.remove_exam_question import RemoveExamQuestion, RemoveExamQuestionHandler
from app.modules.assessment.application.commands.reorder_exam_questions import ReorderExamQuestions, ReorderExamQuestionsHandler
from app.modules.assessment.application.commands.save_answer import SaveAnswer, SaveAnswerHandler
from app.modules.assessment.application.commands.set_question_points import SetQuestionPoints, SetQuestionPointsHandler
from app.modules.assessment.application.commands.start_attempt import StartAttempt, StartAttemptHandler
from app.modules.assessment.application.commands.submit_attempt import SubmitAttempt, SubmitAttemptHandler
from app.modules.assessment.application.commands.swap_exam_question import SwapExamQuestion, SwapExamQuestionHandler
from app.modules.assessment.application.commands.update_assignment import UpdateAssignment, UpdateAssignmentHandler
from app.modules.assessment.application.commands.update_exam import UpdateExam, UpdateExamHandler
from app.modules.assessment.application.queries.assignment_report import AssignmentReport, AssignmentReportHandler
from app.modules.assessment.application.queries.attempt_result import AttemptResult, AttemptResultHandler
from app.modules.assessment.application.queries.get_assignment import GetAssignment, GetAssignmentHandler
from app.modules.assessment.application.queries.get_attempt import GetAttempt, GetAttemptHandler
from app.modules.assessment.application.queries.get_exam import GetExam, GetExamHandler
from app.modules.assessment.application.queries.my_assignments import MyAssignmentsHandler
from app.modules.assessment.application.queries.search_assignments import SearchAssignments, SearchAssignmentsHandler
from app.modules.assessment.application.queries.search_exam_questions import SearchExamQuestions, SearchExamQuestionsHandler
from app.modules.assessment.application.queries.search_exams import SearchExams, SearchExamsHandler
from app.modules.assessment.interface import deps
from app.modules.assessment.interface.schemas import (
    AnswerIn,
    AssignmentIn,
    AssignmentOut,
    AssignmentPatch,
    BlueprintIn,
    BlueprintOut,
    ExamIn,
    ExamOut,
    ExamPatch,
    ExamQuestionOut,
    GradeIn,
    IdsIn,
    MyAssignmentOut,
    PointsIn,
    StartOut,
    assignment_out,
    assignment_view_out,
    exam_out,
    exam_question_out,
    exam_row_out,
    my_assignment_out,
)
from app.shared.application.actor import Actor
from app.shared.domain.clock import utcnow
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut, SearchBody

router = APIRouter(tags=["assessment"])


def _page(page, out) -> PageOut:
    return PageOut(data=[out(v) for v in page.data], total=page.total, page=page.page, limit=page.limit)


def _server_time(response: Response) -> None:
    response.headers["X-Server-Time"] = utcnow().isoformat()


# ------------------------------------------------------------------ exams


@router.post("/exams/search", response_model=PageOut[ExamOut])
def search_exams(body: SearchBody, actor: Actor = Depends(staff_actor), handle: SearchExamsHandler = Depends(deps.search_exams)):
    """Filters: title (text) · grade (number) · source (enum) · subject_id (uuid) · created_at (date); sort also by
    question_count, total_points. Newest first; personal review exams are left out; rows never embed questions."""
    return _page(handle(actor, SearchExams(body.to_request())), exam_row_out)


@router.post("/exams", response_model=ExamOut, status_code=201)
def create_exam(body: ExamIn, actor: Actor = Depends(staff_actor), handle: CreateExamHandler = Depends(deps.create_exam),
                present: GetExamHandler = Depends(deps.get_exam)):
    exam_id = handle(actor, CreateExam(body.title, body.subject_id, body.grade, body.description, body.settings))
    return exam_out(present(actor, GetExam(exam_id)))


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: uuid.UUID, actor: Actor = Depends(staff_actor), present: GetExamHandler = Depends(deps.get_exam)):
    return exam_out(present(actor, GetExam(exam_id)))


@router.post("/exams/{exam_id}/questions/search", response_model=PageOut[ExamQuestionOut])
def search_exam_questions(exam_id: uuid.UUID, body: SearchBody, actor: Actor = Depends(staff_actor),
                          handle: SearchExamQuestionsHandler = Depends(deps.search_exam_questions)):
    """Filters: stem (text) · type, section (enum) · position, points (number); by position unless sorted."""
    return _page(handle(actor, SearchExamQuestions(exam_id, body.to_request())), exam_question_out)


@router.patch("/exams/{exam_id}", response_model=ExamOut)
def patch_exam(exam_id: uuid.UUID, body: ExamPatch, actor: Actor = Depends(staff_actor), handle: UpdateExamHandler = Depends(deps.update_exam),
               present: GetExamHandler = Depends(deps.get_exam)):
    handle(actor, UpdateExam(exam_id, body.model_dump(exclude_unset=True)))
    return exam_out(present(actor, GetExam(exam_id)))


@router.delete("/exams/{exam_id}", status_code=204)
def delete_exam(exam_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteExamHandler = Depends(deps.delete_exam)):
    handle(actor, DeleteExam(exam_id))
    return Response(status_code=204)


@router.post("/exams/{exam_id}/blueprint", response_model=BlueprintOut)
def blueprint(exam_id: uuid.UUID, body: BlueprintIn, actor: Actor = Depends(staff_actor),
              handle: ApplyBlueprintHandler = Depends(deps.apply_blueprint), present: GetExamHandler = Depends(deps.get_exam)):
    r = handle(actor, ApplyBlueprint(exam_id, body.rows, body.seed, body.replace))
    return BlueprintOut(**r, exam=exam_out(present(actor, GetExam(exam_id))))


@router.post("/exams/{exam_id}/questions", response_model=ExamOut)
def add_questions(exam_id: uuid.UUID, body: IdsIn, actor: Actor = Depends(staff_actor),
                  handle: AddExamQuestionsHandler = Depends(deps.add_exam_questions), present: GetExamHandler = Depends(deps.get_exam)):
    handle(actor, AddExamQuestions(exam_id, body.question_ids))
    return exam_out(present(actor, GetExam(exam_id)))


@router.delete("/exams/{exam_id}/questions/{qid}", response_model=ExamOut)
def remove_question(exam_id: uuid.UUID, qid: uuid.UUID, actor: Actor = Depends(staff_actor),
                    handle: RemoveExamQuestionHandler = Depends(deps.remove_exam_question), present: GetExamHandler = Depends(deps.get_exam)):
    handle(actor, RemoveExamQuestion(exam_id, qid))
    return exam_out(present(actor, GetExam(exam_id)))


@router.put("/exams/{exam_id}/order", response_model=ExamOut)
def reorder(exam_id: uuid.UUID, body: IdsIn, actor: Actor = Depends(staff_actor),
            handle: ReorderExamQuestionsHandler = Depends(deps.reorder_exam_questions), present: GetExamHandler = Depends(deps.get_exam)):
    """The draft's order as arranged by the teacher (exactly the exam's questions)."""
    handle(actor, ReorderExamQuestions(exam_id, body.question_ids))
    return exam_out(present(actor, GetExam(exam_id)))


@router.post("/exams/{exam_id}/questions/{qid}/swap", response_model=ExamOut)
def swap(exam_id: uuid.UUID, qid: uuid.UUID, actor: Actor = Depends(staff_actor),
         handle: SwapExamQuestionHandler = Depends(deps.swap_exam_question), present: GetExamHandler = Depends(deps.get_exam)):
    handle(actor, SwapExamQuestion(exam_id, qid))
    return exam_out(present(actor, GetExam(exam_id)))


@router.patch("/exams/{exam_id}/questions/{qid}", response_model=ExamOut)
def set_points(exam_id: uuid.UUID, qid: uuid.UUID, body: PointsIn, actor: Actor = Depends(staff_actor),
               handle: SetQuestionPointsHandler = Depends(deps.set_question_points), present: GetExamHandler = Depends(deps.get_exam)):
    handle(actor, SetQuestionPoints(exam_id, qid, body.points))
    return exam_out(present(actor, GetExam(exam_id)))


# ------------------------------------------------------------------ assignments


@router.post("/assignments/search", response_model=PageOut[AssignmentOut])
def search_assignments(body: SearchBody, actor: Actor = Depends(staff_actor),
                       handle: SearchAssignmentsHandler = Depends(deps.search_assignments)):
    """Filters: title (text) · exam_id (uuid) · open_at, close_at (date) · duration_minutes (number); newest window first."""
    return _page(handle(actor, SearchAssignments(body.to_request())), assignment_view_out)


@router.post("/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(body: AssignmentIn, actor: Actor = Depends(staff_actor),
                      handle: CreateAssignmentHandler = Depends(deps.create_assignment),
                      present: GetAssignmentHandler = Depends(deps.get_assignment)):
    a = handle(actor, CreateAssignment(**body.model_dump()))
    return assignment_view_out(present(actor, GetAssignment(a.id)))


@router.get("/assignments/{aid}", response_model=AssignmentOut)
def get_assignment(aid: uuid.UUID, actor: Actor = Depends(staff_actor), present: GetAssignmentHandler = Depends(deps.get_assignment)):
    return assignment_view_out(present(actor, GetAssignment(aid)))


@router.patch("/assignments/{aid}", response_model=AssignmentOut)
def patch_assignment(aid: uuid.UUID, body: AssignmentPatch, actor: Actor = Depends(staff_actor),
                     handle: UpdateAssignmentHandler = Depends(deps.update_assignment)):
    return assignment_out(handle(actor, UpdateAssignment(aid, body.model_dump(exclude_unset=True))))


@router.delete("/assignments/{aid}", status_code=204)
def delete_assignment(aid: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteAssignmentHandler = Depends(deps.delete_assignment)):
    handle(actor, DeleteAssignment(aid))
    return Response(status_code=204)


@router.get("/assignments/{aid}/report")
def assignment_report(aid: uuid.UUID, actor: Actor = Depends(current_actor), handle: AssignmentReportHandler = Depends(deps.assignment_report)):
    """Per student (best score on the exam's scale) and per question (success ratio, most chosen wrong option)."""
    return handle(actor, AssignmentReport(aid))


@router.get("/me/assignments", response_model=list[MyAssignmentOut])
def my_assignments(actor: Actor = Depends(current_actor), handle: MyAssignmentsHandler = Depends(deps.my_assignments)):
    return [my_assignment_out(v) for v in handle(actor)]


@router.post("/assignments/{aid}/start", response_model=StartOut)
def start(aid: uuid.UUID, actor: Actor = Depends(current_actor), handle: StartAttemptHandler = Depends(deps.start_attempt)):
    return StartOut(attempt_id=handle(actor, StartAttempt(aid)))


# ------------------------------------------------------------------ attempts


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: uuid.UUID, response: Response, actor: Actor = Depends(current_actor),
                handle: GetAttemptHandler = Depends(deps.get_attempt)):
    """The runner's view (no keys); `X-Server-Time` and `server_now` let the timer follow the server's clock."""
    view = handle(actor, GetAttempt(attempt_id))
    _server_time(response)
    return view


@router.put("/attempts/{attempt_id}/answers/{qid}")
def save_answer(attempt_id: uuid.UUID, qid: uuid.UUID, body: AnswerIn, response: Response, actor: Actor = Depends(current_actor),
                handle: SaveAnswerHandler = Depends(deps.save_answer)):
    saved = handle(actor, SaveAnswer(attempt_id, qid, body.response))
    _server_time(response)
    return saved


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: SubmitAttemptHandler = Depends(deps.submit_attempt)):
    return handle(actor, SubmitAttempt(attempt_id))


@router.post("/attempts/{attempt_id}/tab-switch")
def tab_switch(attempt_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: RecordTabSwitchHandler = Depends(deps.record_tab_switch)):
    return {"tab_switches": handle(actor, RecordTabSwitch(attempt_id))}


@router.get("/attempts/{attempt_id}/result")
def result(attempt_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: AttemptResultHandler = Depends(deps.attempt_result)):
    """Hidden (with the reason and, after close, when) unless the assignment's policy shows it; staff always see it."""
    return handle(actor, AttemptResult(attempt_id))


@router.patch("/attempts/{attempt_id}/answers/{qid}/grade")
def grade(attempt_id: uuid.UUID, qid: uuid.UUID, body: GradeIn, actor: Actor = Depends(current_actor),
          handle: GradeEssayHandler = Depends(deps.grade_essay)):
    return handle(actor, GradeEssay(attempt_id, qid, body.points, body.comment))
