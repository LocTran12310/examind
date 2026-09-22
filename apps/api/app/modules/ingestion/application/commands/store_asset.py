from dataclasses import dataclass
import uuid

from app.modules.ingestion.domain.entities import Asset
from app.modules.ingestion.domain.ports import AssetRepository, FileStorage
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid
from app.shared.domain.ids import new_id
from app.shared.domain.images import ALLOWED, sniff

MAX_BYTES = 10 * 1024 * 1024


class StoreImage:
    """An image into object storage + its asset row (flushed; the caller owns the transaction). Raises Invalid."""

    def __init__(self, assets: AssetRepository, files: FileStorage):
        self.assets, self.files = assets, files

    def __call__(self, org_id: uuid.UUID, data: bytes, source_document_id: uuid.UUID | None = None, page: int | None = None) -> Asset:
        if len(data) > MAX_BYTES:
            raise Invalid("Ảnh tối đa 10MB", "file")
        mime, w, h = sniff(data)
        if mime not in ALLOWED:
            raise Invalid("Chỉ hỗ trợ ảnh PNG, JPEG, GIF, WEBP", "file")
        aid = new_id()
        key = f"{org_id}/assets/{aid}.{ALLOWED[mime]}"
        self.files.put(key, data, mime)
        asset = Asset(id=aid, organization_id=org_id, storage_key=key, mime=mime, size=len(data), width=w, height=h,
                      source_document_id=source_document_id, page=page)
        self.assets.add(asset)
        return asset


@dataclass(frozen=True)
class UploadAsset:
    data: bytes


class UploadAssetHandler:
    """A picture pasted into the question editor."""

    def __init__(self, store: StoreImage, uow: UnitOfWork):
        self.store, self.uow = store, uow

    def __call__(self, actor: Actor, cmd: UploadAsset) -> Asset:
        asset = self.store(actor.org_id, cmd.data)
        self.uow.commit()
        return asset
