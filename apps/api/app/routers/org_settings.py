from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope
from app.routers.users import staff_scope
from app.services import ingestion_settings

router = APIRouter(prefix="/org/settings", tags=["org-settings"])


@router.get("/ingestion")
def get_ingestion(scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return ingestion_settings.org_defaults(db, scope.org_id)


@router.put("/ingestion")
def put_ingestion(body: dict, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return ingestion_settings.save_org_defaults(db, scope, body)
