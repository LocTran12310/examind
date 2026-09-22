"""Store images found during extraction as org assets linked to the source document."""
import uuid

from app.modules.ingestion.application.commands.store_asset import StoreImage
from app.modules.ingestion.domain.ports import ImageStore, VectorImages
from app.shared.domain.errors import Invalid


def document_store(images: StoreImage, vector: VectorImages, org_id: uuid.UUID, document_id: uuid.UUID | None,
                   warnings: list[str], stats: dict | None = None) -> ImageStore:
    def store(data: bytes, page: int | None = None) -> str | None:
        if vector.kind(data):  # WMF/EMF: browsers cannot show them
            png = vector.to_png(data)
            if png == b"":
                return None  # a blank picture: nothing lost
            if stats is not None:
                key = "vector_images" if png else "vector_failed"
                stats[key] = stats.get(key, 0) + 1
            if png:
                data = png
        try:
            asset = images(org_id, data, source_document_id=document_id, page=page)
        except Invalid:
            warnings.append("Bỏ qua một hình không hỗ trợ (EMF/WMF/SVG hoặc quá lớn)")
            return None
        return str(asset.id)

    return store
