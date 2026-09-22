"""The ImageStore of one document on a session: pictures go through LibreOffice when they are metafiles, then into
object storage as assets of the document."""
import uuid

from sqlalchemy.orm import Session

from app.modules.ingestion.application.commands.store_asset import StoreImage
from app.modules.ingestion.application.image_store import document_store as _document_store
from app.modules.ingestion.domain.ports import ImageStore
from app.modules.ingestion.infrastructure.adapters.storage import S3FileStorage
from app.modules.ingestion.infrastructure.adapters.vector_images import LibreOfficeVectorImages
from app.modules.ingestion.infrastructure.repositories import SqlAssetRepository


def document_store(db: Session, org_id: uuid.UUID, document_id: uuid.UUID | None, warnings: list[str], stats: dict | None = None) -> ImageStore:
    return _document_store(StoreImage(SqlAssetRepository(db), S3FileStorage()), LibreOfficeVectorImages(), org_id, document_id, warnings, stats)
