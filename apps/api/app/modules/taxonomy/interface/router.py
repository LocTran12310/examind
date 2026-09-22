import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.taxonomy.application.commands.create_tag import CreateTag, CreateTagHandler
from app.modules.taxonomy.application.commands.delete_tag import DeleteTag, DeleteTagHandler
from app.modules.taxonomy.application.commands.update_tag import UNCHANGED, UpdateTag, UpdateTagHandler
from app.modules.taxonomy.application.queries.search_tags import SearchTags, SearchTagsHandler
from app.modules.taxonomy.interface import deps
from app.modules.taxonomy.interface.schemas import TagIn, TagOut, TagSearchBody, TagUpdate
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut

router = APIRouter(tags=["taxonomy"])


@router.post("/tags/search", response_model=PageOut[TagOut])
def search_tags(body: TagSearchBody, actor: Actor = Depends(current_actor), handle: SearchTagsHandler = Depends(deps.search_tags)):
    """Filters: group (enum) · name (text) · subject_id (uuid)."""
    page = handle(actor, SearchTags(body.to_request(), body.subject_id, body.include_shared))
    return PageOut(data=[TagOut(**vars(t)) for t in page.data], total=page.total, page=page.page, limit=page.limit)


@router.post("/tags", response_model=TagOut, status_code=201)
def create_tag(body: TagIn, actor: Actor = Depends(staff_actor), handle: CreateTagHandler = Depends(deps.create_tag)):
    return TagOut(**vars(handle(actor, CreateTag(body.group, body.name, body.subject_id))))


@router.patch("/tags/{tag_id}", response_model=TagOut)
def update_tag(tag_id: uuid.UUID, body: TagUpdate, actor: Actor = Depends(staff_actor), handle: UpdateTagHandler = Depends(deps.update_tag)):
    subject = body.subject_id if "subject_id" in body.model_fields_set else UNCHANGED
    return TagOut(**vars(handle(actor, UpdateTag(tag_id, body.group, body.name, subject))))


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteTagHandler = Depends(deps.delete_tag)):
    handle(actor, DeleteTag(tag_id))
    return Response(status_code=204)
