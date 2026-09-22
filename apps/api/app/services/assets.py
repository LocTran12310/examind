"""Assets moved to the ingestion module (architecture-refactor UOW-05); the demo-question seeder (old layout) stores
its pictures here."""
from sqlalchemy.orm import Session

from app.modules.ingestion.application.commands.store_asset import StoreImage
from app.modules.ingestion.domain.entities import Asset
from app.modules.ingestion.infrastructure.adapters.storage import S3FileStorage
from app.modules.ingestion.infrastructure.repositories import SqlAssetRepository


def store_image(db: Session, org_id, data: bytes) -> Asset:
    return StoreImage(SqlAssetRepository(db), S3FileStorage())(org_id, data)
