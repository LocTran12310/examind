"""Builds the ingestion handlers (composition of ports and adapters). The bank, the taxonomy's source tags and the
assessment context's exams are reached through factories the composition root registers: ingestion never imports
another module."""
from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.ingestion.application.api import IngestionApi
from app.modules.ingestion.application.commands.create_exam_from_document import CreateExamFromDocumentHandler
from app.modules.ingestion.application.commands.delete_ai_model import DeleteAiModelHandler
from app.modules.ingestion.application.commands.delete_document import DeleteDocumentHandler
from app.modules.ingestion.application.commands.ingest_document import IngestDocumentHandler, MarkIngestFailedHandler
from app.modules.ingestion.application.commands.reparse_document import ReparseDocumentHandler
from app.modules.ingestion.application.commands.save_ai_model import CreateAiModelHandler, UpdateAiModelHandler
from app.modules.ingestion.application.commands.save_ingestion_settings import SaveIngestionSettingsHandler
from app.modules.ingestion.application.commands.store_asset import StoreImage, UploadAssetHandler
from app.modules.ingestion.application.commands.update_document_meta import UpdateDocumentMetaHandler
from app.modules.ingestion.application.commands.upload_document import UploadDocumentHandler
from app.modules.ingestion.application.image_store import document_store
from app.modules.ingestion.application.queries.ai_models import DiscoverModelsHandler, SearchAiModelsHandler, TestAiModelHandler
from app.modules.ingestion.application.queries.check_duplicates import CheckDuplicatesHandler
from app.modules.ingestion.application.queries.get_asset import GetAssetHandler
from app.modules.ingestion.application.queries.get_document import DocumentFileHandler, GetDocumentHandler, PageImageHandler
from app.modules.ingestion.application.queries.ingestion_settings import GetIngestionSettingsHandler
from app.modules.ingestion.application.queries.search_documents import SearchDocumentsHandler
from app.modules.ingestion.application.stages.ai_split import AiSplitter
from app.modules.ingestion.application.stages.extract import Extractor
from app.modules.ingestion.application.stages.topic_suggest import TopicSuggester
from app.modules.ingestion.domain.ports import ExamDrafts, QuestionBank
from app.modules.ingestion.infrastructure.adapters.crypto import FernetKeyCipher
from app.modules.ingestion.infrastructure.adapters.llm import HttpChatModels
from app.modules.ingestion.infrastructure.adapters.pandoc import PandocDocxReader
from app.modules.ingestion.infrastructure.adapters.pdf import PdfiumPageRenderer, PdfplumberReader
from app.modules.ingestion.infrastructure.adapters.settings import SqlOrgSettings
from app.modules.ingestion.infrastructure.adapters.storage import S3FileStorage
from app.modules.ingestion.infrastructure.adapters.taxonomy import SqlTaxonomyLookup
from app.modules.ingestion.infrastructure.adapters.tesseract import TesseractScanner
from app.modules.ingestion.infrastructure.adapters.vector_images import LibreOfficeVectorImages
from app.modules.ingestion.infrastructure.read_models import SqlAiModelReader, SqlDocumentReader
from app.modules.ingestion.infrastructure.repositories import SqlAiModelRepository, SqlAssetRepository, SqlDocumentRepository
from app.shared.domain.clock import utcnow
from app.shared.infrastructure.config import get_settings
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_audit import SqlAuditTrail
from app.shared.infrastructure.sql_jobs import SqlJobQueue
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork

_bank: Callable[[Session], QuestionBank] | None = None
_source_tags: Callable[[Session], object] | None = None
_exams: Callable[[Session], ExamDrafts] | None = None


def register_bank(factory: Callable[[Session], QuestionBank]) -> None:
    global _bank
    _bank = factory


def register_source_tags(factory: Callable[[Session], object]) -> None:
    """Something with `source_tag(org_id, name) -> tag id` (the taxonomy API)."""
    global _source_tags
    _source_tags = factory


def register_exam_drafts(factory: Callable[[Session], ExamDrafts]) -> None:
    global _exams
    _exams = factory


def _registered(factory, what: str):
    if factory is None:
        raise RuntimeError(f"no {what} registered")
    return factory


def _taxonomy(db: Session) -> SqlTaxonomyLookup:
    return SqlTaxonomyLookup(db, _source_tags(db) if _source_tags else None)


def _bank_of(db: Session) -> QuestionBank:
    return _registered(_bank, "question bank")(db)


def ingestion_api(db: Session) -> IngestionApi:
    """Ingestion for another context (the bank's tagging queue asks it for topic candidates), on the caller's session."""
    return IngestionApi(_taxonomy(db), _bank_of(db))


# ------------------------------------------------------------------ worker


def ingest_document(db: Session) -> IngestDocumentHandler:
    """The pipeline for the worker, on the job's session."""
    models, chat, scanner = SqlAiModelRepository(db), HttpChatModels(), TesseractScanner()
    ai = AiSplitter(models, chat, scanner)
    store = StoreImage(SqlAssetRepository(db), S3FileStorage())
    vector = LibreOfficeVectorImages()
    taxonomy, bank = _taxonomy(db), _bank_of(db)
    return IngestDocumentHandler(
        SqlDocumentRepository(db), S3FileStorage(),
        lambda doc, warnings, stats: document_store(store, vector, doc.organization_id, doc.id, warnings, stats),
        Extractor(PandocDocxReader(), PdfplumberReader(), scanner, ai), ai, taxonomy, bank,
        TopicSuggester(taxonomy, bank, models, chat), utcnow, SqlUnitOfWork(db))


def mark_ingest_failed(db: Session) -> MarkIngestFailedHandler:
    return MarkIngestFailedHandler(SqlDocumentRepository(db), utcnow, SqlUnitOfWork(db))


# ------------------------------------------------------------------ documents


def search_documents(db: Session = Depends(get_db)) -> SearchDocumentsHandler:
    return SearchDocumentsHandler(SqlDocumentReader(db))


def get_document(db: Session = Depends(get_db)) -> GetDocumentHandler:
    return GetDocumentHandler(SqlDocumentRepository(db))


def document_file(db: Session = Depends(get_db)) -> DocumentFileHandler:
    return DocumentFileHandler(SqlDocumentRepository(db), S3FileStorage())


def page_image(db: Session = Depends(get_db)) -> PageImageHandler:
    return PageImageHandler(SqlDocumentRepository(db), S3FileStorage(), PdfiumPageRenderer())


def check_duplicates(db: Session = Depends(get_db)) -> CheckDuplicatesHandler:
    return CheckDuplicatesHandler(SqlDocumentRepository(db))


def _reparse(db: Session) -> ReparseDocumentHandler:
    return ReparseDocumentHandler(SqlDocumentRepository(db), SqlOrgSettings(db), SqlJobQueue(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def _update_meta(db: Session) -> UpdateDocumentMetaHandler:
    return UpdateDocumentMetaHandler(SqlDocumentRepository(db), _taxonomy(db), _bank_of(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def reparse_document(db: Session = Depends(get_db)) -> ReparseDocumentHandler:
    return _reparse(db)


def update_document_meta(db: Session = Depends(get_db)) -> UpdateDocumentMetaHandler:
    return _update_meta(db)


def upload_document(db: Session = Depends(get_db)) -> UploadDocumentHandler:
    return UploadDocumentHandler(SqlDocumentRepository(db), S3FileStorage(), SqlOrgSettings(db), _taxonomy(db), SqlJobQueue(db),
                                 SqlAuditTrail(db), _reparse(db), _update_meta(db), SqlUnitOfWork(db))


def delete_document(db: Session = Depends(get_db)) -> DeleteDocumentHandler:
    return DeleteDocumentHandler(SqlDocumentRepository(db), S3FileStorage(), _bank_of(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def create_exam_from_document(db: Session = Depends(get_db)) -> CreateExamFromDocumentHandler:
    return CreateExamFromDocumentHandler(SqlDocumentRepository(db), _registered(_exams, "exam drafts")(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ assets


def upload_asset(db: Session = Depends(get_db)) -> UploadAssetHandler:
    return UploadAssetHandler(StoreImage(SqlAssetRepository(db), S3FileStorage()), SqlUnitOfWork(db))


def get_asset(db: Session = Depends(get_db)) -> GetAssetHandler:
    return GetAssetHandler(SqlAssetRepository(db), S3FileStorage())


# ------------------------------------------------------------------ AI models and settings


def search_ai_models(db: Session = Depends(get_db)) -> SearchAiModelsHandler:
    return SearchAiModelsHandler(SqlAiModelReader(db))


def create_ai_model(db: Session = Depends(get_db)) -> CreateAiModelHandler:
    return CreateAiModelHandler(SqlAiModelRepository(db), FernetKeyCipher(), SqlAuditTrail(db), SqlUnitOfWork(db))


def update_ai_model(db: Session = Depends(get_db)) -> UpdateAiModelHandler:
    return UpdateAiModelHandler(SqlAiModelRepository(db), FernetKeyCipher(), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_ai_model(db: Session = Depends(get_db)) -> DeleteAiModelHandler:
    return DeleteAiModelHandler(SqlAiModelRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def discover_models() -> DiscoverModelsHandler:
    return DiscoverModelsHandler(HttpChatModels(), get_settings().ollama_url)


def test_ai_model(db: Session = Depends(get_db)) -> TestAiModelHandler:
    return TestAiModelHandler(SqlAiModelRepository(db), HttpChatModels())


def get_ingestion_settings(db: Session = Depends(get_db)) -> GetIngestionSettingsHandler:
    return GetIngestionSettingsHandler(SqlOrgSettings(db))


def save_ingestion_settings(db: Session = Depends(get_db)) -> SaveIngestionSettingsHandler:
    return SaveIngestionSettingsHandler(SqlOrgSettings(db), SqlAiModelRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))
