import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import storage
from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.routers.users import staff_scope
from app.services import assets

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    a = assets.store_image(db, scope.org_id, await file.read())
    return {"id": a.id, "mime": a.mime, "width": a.width, "height": a.height, "ref": f"asset:{a.id}"}


@router.get("/{asset_id}")
def fetch(asset_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    a = assets.get_asset(db, scope.org_id, asset_id)
    data, _ = storage.get(a.storage_key)
    return Response(content=data, media_type=a.mime, headers={
        "Cache-Control": "private, max-age=86400, immutable",
        "X-Content-Type-Options": "nosniff",
    })
