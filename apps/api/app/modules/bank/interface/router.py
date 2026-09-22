import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.bank.application.commands.apply_answer_key import ApplyAnswerKey, ApplyAnswerKeyHandler
from app.modules.bank.application.commands.approve_confident import ApproveConfident, ApproveConfidentHandler
from app.modules.bank.application.commands.assign_reviewer import AssignReviewer, AssignReviewerHandler
from app.modules.bank.application.commands.audit_keys import AuditKeys, AuditKeysHandler
from app.modules.bank.application.commands.bulk_update_questions import BulkUpdateQuestions, BulkUpdateQuestionsHandler
from app.modules.bank.application.commands.create_question import CreateQuestion, CreateQuestionHandler
from app.modules.bank.application.commands.delete_question import DeleteQuestion, DeleteQuestionHandler
from app.modules.bank.application.commands.review_question import ReviewQuestion, ReviewQuestionHandler
from app.modules.bank.application.commands.update_question import UpdateQuestion, UpdateQuestionHandler
from app.modules.bank.application.queries.demo_question import DemoQuestionHandler
from app.modules.bank.application.queries.document_questions import DocumentQuestionsHandler, DocumentQuestionsQuery
from app.modules.bank.application.queries.get_question import GetQuestion, GetQuestionHandler
from app.modules.bank.application.queries.get_review_document import GetReviewDocument, GetReviewDocumentHandler
from app.modules.bank.application.queries.question_facets import QuestionFacets, QuestionFacetsHandler
from app.modules.bank.application.queries.review_queue import ReviewQueue, ReviewQueueHandler
from app.modules.bank.application.queries.search_flagged import SearchFlagged, SearchFlaggedHandler
from app.modules.bank.application.queries.search_questions import SearchQuestions, SearchQuestionsHandler
from app.modules.bank.application.queries.search_review_documents import SearchReviewDocuments, SearchReviewDocumentsHandler
from app.modules.bank.interface import deps
from app.modules.bank.interface.schemas import (
    ActionIn,
    AnswerKeyIn,
    AnswerKeyOut,
    ApprovedOut,
    AssignIn,
    BulkIn,
    BulkOut,
    FacetsOut,
    FlaggedIdsOut,
    ParsedQuestionOut,
    QuestionCreate,
    QuestionOut,
    QuestionPatch,
    QuestionSearchBody,
    ReviewDocumentOut,
    ReviewDocumentSearchBody,
    parsed_out,
    question_out,
    review_document_out,
)
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut, SearchBody

router = APIRouter(tags=["bank"])


def _page(page, out) -> PageOut:
    return PageOut(data=[out(v) for v in page.data], total=page.total, page=page.page, limit=page.limit)


# ------------------------------------------------------------------ questions


@router.post("/questions/search", response_model=PageOut[ParsedQuestionOut])
def search_questions(body: QuestionSearchBody, actor: Actor = Depends(staff_actor),
                     handle: SearchQuestionsHandler = Depends(deps.search_questions)):
    """Bank filters at the top of the body; filters: stem (text) · created_at, updated_at (date) · number, grade (number);
    sort also by difficulty, type, confidence. Relevance first when `q` is given, then newest."""
    return _page(handle(actor, SearchQuestions(body.to_request(), body.to_filters())), parsed_out)


@router.post("/questions/facets", response_model=FacetsOut)
def question_facets(body: QuestionSearchBody, actor: Actor = Depends(staff_actor),
                    handle: QuestionFacetsHandler = Depends(deps.question_facets)):
    """Counts per subject / topic (subtree) / type / difficulty / grade / đợt / năm học / tag for the filter sheet;
    same body as the search, each facet ignores its own filter."""
    return handle(actor, QuestionFacets(body.to_request(), body.to_filters()))


@router.post("/questions", response_model=ParsedQuestionOut, status_code=201)
def create_question(body: QuestionCreate, actor: Actor = Depends(staff_actor), handle: CreateQuestionHandler = Depends(deps.create_question)):
    return parsed_out(handle(actor, CreateQuestion(**{k: v for k, v in body.model_dump().items() if v is not None})))


@router.post("/questions/bulk", response_model=BulkOut)
def bulk_questions(body: BulkIn, actor: Actor = Depends(staff_actor), handle: BulkUpdateQuestionsHandler = Depends(deps.bulk_update_questions)):
    s = body.set
    return BulkOut(updated=handle(actor, BulkUpdateQuestions(body.ids, s.status, s.difficulty, s.primary_topic_id, s.add_tag_ids)))


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteQuestionHandler = Depends(deps.delete_question)):
    handle(actor, DeleteQuestion(question_id))
    return Response(status_code=204)


@router.get("/questions/demo", response_model=QuestionOut)
def demo(actor: Actor = Depends(current_actor), handle: DemoQuestionHandler = Depends(deps.demo_question)):
    return question_out(handle(actor))


@router.get("/questions/{question_id}")
def get_question(question_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: GetQuestionHandler = Depends(deps.get_question)):
    """Students get the question without answer or solution."""
    v = handle(actor, GetQuestion(question_id))
    return question_out(v) if actor.role == "student" else parsed_out(v)


@router.patch("/questions/{question_id}", response_model=ParsedQuestionOut)
def patch_question(question_id: uuid.UUID, body: QuestionPatch, actor: Actor = Depends(staff_actor),
                   handle: UpdateQuestionHandler = Depends(deps.update_question)):
    sent = body.model_dump(exclude_unset=True)
    return parsed_out(handle(actor, UpdateQuestion(question_id, **{k: v for k, v in sent.items() if v is not None}, sent=frozenset(sent))))


# ------------------------------------------------------------------ review


@router.post("/review/documents/search", response_model=PageOut[ReviewDocumentOut])
def review_documents(body: ReviewDocumentSearchBody, actor: Actor = Depends(staff_actor),
                     handle: SearchReviewDocumentsHandler = Depends(deps.search_review_documents)):
    """Filters: filename, source_name (text) · assigned_to (uuid) · created_at (date); sort also by total, needs_review."""
    return _page(handle(actor, SearchReviewDocuments(body.to_request(), body.mine)), review_document_out)


@router.get("/review/documents/{doc_id}", response_model=ReviewDocumentOut)
def review_document(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: GetReviewDocumentHandler = Depends(deps.get_review_document)):
    return review_document_out(handle(actor, GetReviewDocument(doc_id)))


@router.patch("/review/documents/{doc_id}", response_model=ReviewDocumentOut)
def assign(doc_id: uuid.UUID, body: AssignIn, actor: Actor = Depends(staff_actor), handle: AssignReviewerHandler = Depends(deps.assign_reviewer)):
    return review_document_out(handle(actor, AssignReviewer(doc_id, body.assigned_to)))


@router.get("/review/documents/{doc_id}/queue", response_model=list[ParsedQuestionOut])
def review_queue(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ReviewQueueHandler = Depends(deps.review_queue)):
    return [parsed_out(v) for v in handle(actor, ReviewQueue(doc_id))]


@router.post("/review/questions/{qid}/action", response_model=ParsedQuestionOut)
def question_action(qid: uuid.UUID, body: ActionIn, actor: Actor = Depends(staff_actor), handle: ReviewQuestionHandler = Depends(deps.review_question)):
    return parsed_out(handle(actor, ReviewQuestion(qid, body.action)))


@router.post("/review/documents/{doc_id}/answer-key", response_model=AnswerKeyOut)
def answer_key(doc_id: uuid.UUID, body: AnswerKeyIn, actor: Actor = Depends(staff_actor), handle: ApplyAnswerKeyHandler = Depends(deps.apply_answer_key)):
    return AnswerKeyOut(**vars(handle(actor, ApplyAnswerKey(doc_id, body.text))))


@router.post("/review/documents/{doc_id}/approve-confident", response_model=ApprovedOut)
def approve_confident(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ApproveConfidentHandler = Depends(deps.approve_confident)):
    return ApprovedOut(approved=handle(actor, ApproveConfident(doc_id)))


@router.post("/review/key-audit", response_model=FlaggedIdsOut)
def key_audit(actor: Actor = Depends(staff_actor), handle: AuditKeysHandler = Depends(deps.audit_keys)):
    return FlaggedIdsOut(flagged=[str(i) for i in handle(AuditKeys(actor.org_id))])


@router.post("/review/flagged/search", response_model=PageOut[ParsedQuestionOut])
def flagged(body: SearchBody, actor: Actor = Depends(staff_actor), handle: SearchFlaggedHandler = Depends(deps.search_flagged)):
    """Filters: stem (text) · updated_at (date)."""
    return _page(handle(actor, SearchFlagged(body.to_request())), parsed_out)


# ------------------------------------------------------------------ questions of a source document


@router.get("/documents/{doc_id}/questions", response_model=list[ParsedQuestionOut])
def document_questions(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor),
                       handle: DocumentQuestionsHandler = Depends(deps.document_questions)):
    """Every question parsed from the document (PHẦN then Câu), with topics and tags."""
    return [parsed_out(v) for v in handle(actor, DocumentQuestionsQuery(doc_id))]
