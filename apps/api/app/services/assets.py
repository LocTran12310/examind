import uuid

from sqlalchemy.orm import Session

from app.core import storage
from app.core.errors import not_found, validation
from app.core.images import ALLOWED, sniff
from app.models import Asset

MAX_BYTES = 10 * 1024 * 1024


def store_image(db: Session, org_id, data: bytes) -> Asset:
    if len(data) > MAX_BYTES:
        raise validation("Ảnh tối đa 10MB", "file")
    mime, w, h = sniff(data)
    if mime not in ALLOWED:
        raise validation("Chỉ hỗ trợ ảnh PNG, JPEG, GIF, WEBP", "file")
    aid = uuid.uuid4()
    key = f"{org_id}/assets/{aid}.{ALLOWED[mime]}"
    storage.put(key, data, mime)
    asset = Asset(id=aid, organization_id=org_id, storage_key=key, mime=mime, size=len(data), width=w, height=h)
    db.add(asset)
    db.flush()
    return asset


def get_asset(db: Session, org_id, asset_id) -> Asset:
    a = db.get(Asset, asset_id)
    if a is None or a.organization_id != org_id:
        raise not_found("Không tìm thấy ảnh")
    return a
