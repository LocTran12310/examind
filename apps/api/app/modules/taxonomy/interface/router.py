import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.taxonomy.application.commands.create_tag import CreateTag, CreateTagHandler
from app.modules.taxonomy.application.commands.create_topic import CreateTopic, CreateTopicHandler
from app.modules.taxonomy.application.commands.delete_tag import DeleteTag, DeleteTagHandler
from app.modules.taxonomy.application.commands.delete_topic import DeleteTopic, DeleteTopicHandler
from app.modules.taxonomy.application.commands.merge_topic import MergeTopic, MergeTopicHandler
from app.modules.taxonomy.application.commands.move_topic import MoveTopic, MoveTopicHandler
from app.modules.taxonomy.application.commands.update_tag import UNCHANGED, UpdateTag, UpdateTagHandler
from app.modules.taxonomy.application.commands.update_topic import UpdateTopic, UpdateTopicHandler
from app.modules.taxonomy.application.queries.get_taxonomy import GetTaxonomyHandler
from app.modules.taxonomy.application.queries.list_topics import ListTopics, ListTopicsHandler
from app.modules.taxonomy.application.queries.search_tags import SearchTags, SearchTagsHandler
from app.modules.taxonomy.interface import deps
from app.modules.taxonomy.interface.schemas import (
    GradeOut,
    SemesterOut,
    SubjectOut,
    TagIn,
    TagOut,
    TagSearchBody,
    TagUpdate,
    TaxonomyOut,
    TopicCreate,
    TopicMerge,
    TopicMove,
    TopicOut,
    TopicUpdate,
)
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


@router.get("/taxonomy", response_model=TaxonomyOut)
def taxonomy(actor: Actor = Depends(current_actor), handle: GetTaxonomyHandler = Depends(deps.get_taxonomy)):
    t = handle(actor)
    return TaxonomyOut(subjects=[SubjectOut(**vars(s)) for s in t.subjects], grades=[GradeOut(**vars(g)) for g in t.grades],
                       semesters=[SemesterOut(**vars(s)) for s in t.semesters])


# the knowledge tree is read whole (a tree, not a paged list)
@router.get("/topics", response_model=list[TopicOut])
def list_topics(subject_id: uuid.UUID | None = None, actor: Actor = Depends(current_actor), handle: ListTopicsHandler = Depends(deps.list_topics)):
    return [TopicOut(**vars(t)) for t in handle(actor, ListTopics(subject_id))]


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(body: TopicCreate, actor: Actor = Depends(staff_actor), handle: CreateTopicHandler = Depends(deps.create_topic)):
    return TopicOut(**vars(handle(actor, CreateTopic(body.name, body.subject_id, body.parent_id, body.level_kind, body.grade))))


@router.patch("/topics/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: uuid.UUID, body: TopicUpdate, actor: Actor = Depends(staff_actor), handle: UpdateTopicHandler = Depends(deps.update_topic)):
    return TopicOut(**vars(handle(actor, UpdateTopic(topic_id, body.name, body.level_kind, body.grade, body.sort))))


@router.post("/topics/{topic_id}/move", response_model=TopicOut)
def move_topic(topic_id: uuid.UUID, body: TopicMove, actor: Actor = Depends(staff_actor), handle: MoveTopicHandler = Depends(deps.move_topic)):
    return TopicOut(**vars(handle(actor, MoveTopic(topic_id, body.parent_id))))


@router.post("/topics/{topic_id}/merge", response_model=TopicOut)
def merge_topic(topic_id: uuid.UUID, body: TopicMerge, actor: Actor = Depends(staff_actor), handle: MergeTopicHandler = Depends(deps.merge_topic)):
    return TopicOut(**vars(handle(actor, MergeTopic(topic_id, body.target_id))))


@router.delete("/topics/{topic_id}", status_code=204)
def delete_topic(topic_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: DeleteTopicHandler = Depends(deps.delete_topic)):
    handle(actor, DeleteTopic(topic_id))
    return Response(status_code=204)
