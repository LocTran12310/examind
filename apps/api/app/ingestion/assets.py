"""Store images found during extraction as org assets linked to the source document."""
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.services.assets import store_image

ImageStore = Callable[[bytes, int | None], str | None]


def document_store(db: Session, org_id, document_id, warnings: list[str]) -> ImageStore:
    def store(data: bytes, page: int | None = None) -> str | None:
        try:
            asset = store_image(db, org_id, data)
        except AppError:
            warnings.append("Bỏ qua một hình không hỗ trợ (EMF/WMF/SVG hoặc quá lớn)")
            return None
        asset.source_document_id = document_id
        asset.page = page
        return str(asset.id)

    return store
