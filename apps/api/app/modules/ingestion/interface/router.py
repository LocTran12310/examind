import json
from urllib.parse import quote
import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.modules.ingestion.application.commands.create_exam_from_document import CreateExamFromDocument, CreateExamFromDocumentHandler
from app.modules.ingestion.application.commands.delete_ai_model import DeleteAiModel, DeleteAiModelHandler
from app.modules.ingestion.application.commands.delete_document import DeleteDocument, DeleteDocumentHandler
from app.modules.ingestion.application.commands.reparse_document import ReparseDocument, ReparseDocumentHandler
from app.modules.ingestion.application.commands.save_ai_model import CreateAiModel, CreateAiModelHandler, UpdateAiModel, UpdateAiModelHandler
from app.modules.ingestion.application.commands.save_ingestion_settings import SaveIngestionSettings, SaveIngestionSettingsHandler
from app.modules.ingestion.application.commands.store_asset import UploadAsset, UploadAssetHandler
from app.modules.ingestion.application.commands.update_document_meta import UpdateDocumentMeta, UpdateDocumentMetaHandler
from app.modules.ingestion.application.commands.upload_document import UploadDocument, UploadDocumentHandler
from app.modules.ingestion.application.queries.ai_models import (
    DiscoverModels,
    DiscoverModelsHandler,
    SearchAiModels,
    SearchAiModelsHandler,
    TestAiModel,
    TestAiModelHandler,
)
from app.modules.ingestion.application.queries.check_duplicates import CheckDuplicates, CheckDuplicatesHandler
from app.modules.ingestion.application.queries.get_asset import GetAsset, GetAssetHandler
from app.modules.ingestion.application.queries.get_document import (
    DocumentFileHandler,
    GetDocument,
    GetDocumentHandler,
    GetPageImage,
    PageImageHandler,
)
from app.modules.ingestion.application.queries.ingestion_settings import GetIngestionSettingsHandler
from app.modules.ingestion.application.queries.search_documents import SearchDocuments, SearchDocumentsHandler
from app.modules.ingestion.interface import deps
from app.modules.ingestion.interface.schemas import (
    AiModelIn,
    AiModelOut,
    AiModelUpdate,
    AssetOut,
    DiscoverIn,
    DocumentBrief,
    DocumentCreated,
    DocumentMetaIn,
    DocumentOut,
    DuplicateCheckIn,
    DuplicateOut,
    ExamFromDocumentIn,
    ReparseIn,
    TestResult,
    document_out,
)
from app.shared.application.actor import Actor
from app.shared.domain.errors import Invalid
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut, SearchBody

router = APIRouter(tags=["ingestion"])


def _json_field(raw: str | None, name: str) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise Invalid("JSON không hợp lệ", name) from None
    if not isinstance(value, dict):
        raise Invalid("JSON không hợp lệ", name)
    return value


# ------------------------------------------------------------------ documents


@router.post("/documents/search", response_model=PageOut[DocumentOut])
def search_documents(body: SearchBody, actor: Actor = Depends(staff_actor), handle: SearchDocumentsHandler = Depends(deps.search_documents)):
    """Newest first. Filters: filename, source_name (text) · status, mime (enum) · question_count (number) · created_at (date);
    `q` over filename and source name."""
    page = handle(actor, SearchDocuments(body.to_request()))
    return PageOut(data=[document_out(d) for d in page.data], total=page.total, page=page.page, limit=page.limit)


@router.post("/documents", status_code=201, response_model=DocumentCreated)
async def upload(response: Response, file: UploadFile = File(...), meta: str | None = Form(None), config: str | None = Form(None),
                 on_duplicate: str = Form("skip"), replace_id: uuid.UUID | None = Form(None),
                 actor: Actor = Depends(staff_actor), handle: UploadDocumentHandler = Depends(deps.upload_document)):
    """`on_duplicate`: skip (same content → the existing document) · replace (+ `replace_id` for a same-name file) · keep_both."""
    data = await file.read()
    doc, action = handle(actor, UploadDocument(file.filename or "file", data, _json_field(meta, "meta"), _json_field(config, "config"),
                                               on_duplicate, replace_id))
    if action != "created":
        response.status_code = 200
    return DocumentCreated(document=document_out(doc), duplicate=action != "created", action=action)


@router.post("/documents/check", response_model=list[DuplicateOut])
def check_duplicates(body: DuplicateCheckIn, actor: Actor = Depends(staff_actor), handle: CheckDuplicatesHandler = Depends(deps.check_duplicates)):
    """Before uploading: which files are already here (same content) or share a name with a document."""
    return [DuplicateOut(name=r.name, same_file=DocumentBrief(**vars(r.same_file)) if r.same_file else None,
                         same_name=[DocumentBrief(**vars(d)) for d in r.same_name])
            for r in handle(actor, CheckDuplicates([f.model_dump() for f in body.files]))]


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: GetDocumentHandler = Depends(deps.get_document)):
    return document_out(handle(actor, GetDocument(doc_id)))


@router.get("/documents/{doc_id}/file")
def download(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DocumentFileHandler = Depends(deps.document_file)):
    f = handle(actor, GetDocument(doc_id))
    return Response(content=f.data, media_type=f.mime, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(f.filename)}",
        "X-Content-Type-Options": "nosniff",
    })


@router.patch("/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: uuid.UUID, body: DocumentMetaIn, actor: Actor = Depends(staff_actor),
                    handle: UpdateDocumentMetaHandler = Depends(deps.update_document_meta)):
    return document_out(handle(actor, UpdateDocumentMeta(doc_id, body.meta)))


@router.post("/documents/{doc_id}/exam", status_code=201)
def exam_from_document(doc_id: uuid.UUID, body: ExamFromDocumentIn, actor: Actor = Depends(staff_actor),
                       handle: CreateExamFromDocumentHandler = Depends(deps.create_exam_from_document)):
    return handle(actor, CreateExamFromDocument(doc_id, body.title))


@router.post("/documents/{doc_id}/reparse", response_model=DocumentOut, status_code=202)
def reparse(doc_id: uuid.UUID, body: ReparseIn, actor: Actor = Depends(staff_actor),
            handle: ReparseDocumentHandler = Depends(deps.reparse_document)):
    return document_out(handle(actor, ReparseDocument(doc_id, body.config)))


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteDocumentHandler = Depends(deps.delete_document)):
    handle(actor, DeleteDocument(doc_id))
    return Response(status_code=204)


@router.get("/documents/{doc_id}/pages/{page}.png")
def page_image(doc_id: uuid.UUID, page: int, actor: Actor = Depends(staff_actor), handle: PageImageHandler = Depends(deps.page_image)):
    """Source page for the review queue: PDFs rendered once and cached in object storage; images served as-is."""
    f, immutable = handle(actor, GetPageImage(doc_id, page))
    cache = "private, max-age=86400, immutable" if immutable else "private, max-age=86400"
    return Response(content=f.data, media_type=f.mime, headers={"Cache-Control": cache})


# ------------------------------------------------------------------ assets


@router.post("/assets", status_code=201, response_model=AssetOut)
async def upload_asset(file: UploadFile = File(...), actor: Actor = Depends(staff_actor), handle: UploadAssetHandler = Depends(deps.upload_asset)):
    a = handle(actor, UploadAsset(await file.read()))
    return AssetOut(id=a.id, mime=a.mime, width=a.width, height=a.height, ref=f"asset:{a.id}")


@router.get("/assets/{asset_id}")
def fetch_asset(asset_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: GetAssetHandler = Depends(deps.get_asset)):
    f = handle(actor, GetAsset(asset_id))
    return Response(content=f.data, media_type=f.mime, headers={
        "Cache-Control": "private, max-age=86400, immutable",
        "X-Content-Type-Options": "nosniff",
    })


# ------------------------------------------------------------------ AI models


def _model_out(v) -> AiModelOut:
    return AiModelOut(**vars(v))


@router.post("/ai-models/search", response_model=PageOut[AiModelOut])
def search_ai_models(body: SearchBody, actor: Actor = Depends(current_actor), handle: SearchAiModelsHandler = Depends(deps.search_ai_models)):
    """The org's models and the system ones, system first then by name. Filters: name, model (text) · provider (enum) ·
    enabled, is_free (bool)."""
    page = handle(actor, SearchAiModels(body.to_request()))
    return PageOut(data=[_model_out(v) for v in page.data], total=page.total, page=page.page, limit=page.limit)


@router.post("/ai-models", response_model=AiModelOut, status_code=201)
def create_ai_model(body: AiModelIn, actor: Actor = Depends(current_actor), handle: CreateAiModelHandler = Depends(deps.create_ai_model)):
    return _model_out(handle(actor, CreateAiModel(**body.model_dump())))


@router.post("/ai-models/discover")
def discover(body: DiscoverIn, actor: Actor = Depends(current_actor), handle: DiscoverModelsHandler = Depends(deps.discover_models)):
    return handle(actor, DiscoverModels(body.base_url))


@router.patch("/ai-models/{model_id}", response_model=AiModelOut)
def update_ai_model(model_id: uuid.UUID, body: AiModelUpdate, actor: Actor = Depends(current_actor),
                    handle: UpdateAiModelHandler = Depends(deps.update_ai_model)):
    return _model_out(handle(actor, UpdateAiModel(model_id, body.model_dump())))


@router.delete("/ai-models/{model_id}", status_code=204)
def delete_ai_model(model_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: DeleteAiModelHandler = Depends(deps.delete_ai_model)):
    handle(actor, DeleteAiModel(model_id))
    return Response(status_code=204)


@router.post("/ai-models/{model_id}/test", response_model=TestResult)
def test_ai_model(model_id: uuid.UUID, actor: Actor = Depends(current_actor), handle: TestAiModelHandler = Depends(deps.test_ai_model)):
    return TestResult(**handle(actor, TestAiModel(model_id)))


# ------------------------------------------------------------------ processing defaults of the org


@router.get("/org/settings/ingestion")
def get_ingestion_settings(actor: Actor = Depends(staff_actor), handle: GetIngestionSettingsHandler = Depends(deps.get_ingestion_settings)):
    return handle(actor)


@router.put("/org/settings/ingestion")
def put_ingestion_settings(body: dict, actor: Actor = Depends(staff_actor),
                           handle: SaveIngestionSettingsHandler = Depends(deps.save_ingestion_settings)):
    return handle(actor, SaveIngestionSettings(body))
