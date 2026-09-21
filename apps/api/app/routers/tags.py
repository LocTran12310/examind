import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.routers.users import staff_scope
from app.schemas.taxonomy import TagIn, TagOut, TagUpdate
from app.services import tags

router = APIRouter(prefix="/tags", tags=["tags"])


def _out(t) -> TagOut:
    return TagOut(id=t.id, group=t.group, name=t.name)


@router.get("", response_model=list[TagOut])
def list_tags(group: str | None = None, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    return [_out(t) for t in tags.list_tags(db, scope, group)]


@router.post("", response_model=TagOut, status_code=201)
def create_tag(body: TagIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _out(tags.create_tag(db, scope, body.group, body.name))


@router.patch("/{tag_id}", response_model=TagOut)
def update_tag(tag_id: uuid.UUID, body: TagUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return _out(tags.update_tag(db, scope, tag_id, body.group, body.name))


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    tags.delete_tag(db, scope, tag_id)
    return Response(status_code=204)
