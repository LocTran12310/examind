from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.dto import FileContent
from app.modules.ingestion.domain.ports import AssetRepository, FileStorage
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class GetAsset:
    asset_id: uuid.UUID


class GetAssetHandler:
    def __init__(self, assets: AssetRepository, files: FileStorage):
        self.assets, self.files = assets, files

    def __call__(self, actor: Actor, query: GetAsset) -> FileContent:
        a = self.assets.get(actor.org_id, query.asset_id)
        if a is None:
            raise NotFound("Không tìm thấy ảnh")
        data, _ = self.files.get(a.storage_key)
        return FileContent(data, a.mime)
