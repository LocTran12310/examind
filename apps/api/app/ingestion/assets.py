"""Store images found during extraction as org assets linked to the source document."""
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.ingestion import vector_images
from app.services.assets import store_image

ImageStore = Callable[[bytes, int | None], str | None]


def document_store(db: Session, org_id, document_id, warnings: list[str], stats: dict | None = None) -> ImageStore:
    def store(data: bytes, page: int | None = None) -> str | None:
        if vector_images.kind(data):  # WMF/EMF: browsers cannot show them
            png = vector_images.to_png(data)
            if png == b"":
                return None  # a blank picture: nothing lost
            if stats is not None:
                key = "vector_images" if png else "vector_failed"
                stats[key] = stats.get(key, 0) + 1
            if png:
                data = png
        try:
            asset = store_image(db, org_id, data)
        except AppError:
            warnings.append("Bỏ qua một hình không hỗ trợ (EMF/WMF/SVG hoặc quá lớn)")
            return None
        asset.source_document_id = document_id
        asset.page = page
        return str(asset.id)

    return store
