from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import current_user
from app.models import User
from app.schemas.auth import MyOrgOut
from app.services.membership import orgs_for

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/orgs", response_model=list[MyOrgOut])
def my_orgs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Organisations the header selector offers (all active ones for super admin)."""
    return [MyOrgOut(id=o.id, code=o.code, name=o.name, role=role, is_home=o.id == user.organization_id) for o, role in orgs_for(db, user)]
