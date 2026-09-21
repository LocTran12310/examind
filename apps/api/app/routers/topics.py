import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.routers.users import staff_scope
from app.schemas.taxonomy import TopicCreate, TopicMerge, TopicMove, TopicOut, TopicUpdate, topic_out
from app.services import topics

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(subject_id: uuid.UUID | None = None, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    items, children = topics.list_topics(db, scope, subject_id)
    return [topic_out(t, children.get(t.id, 0)) for t in items]


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(body: TopicCreate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return topic_out(topics.create_topic(db, scope, body.subject_id, body.name, body.parent_id, body.level_kind, body.grade))


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: uuid.UUID, body: TopicUpdate, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return topic_out(topics.update_topic(db, scope, topic_id, **body.model_dump()))


@router.post("/{topic_id}/move", response_model=TopicOut)
def move_topic(topic_id: uuid.UUID, body: TopicMove, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return topic_out(topics.move_topic(db, scope, topic_id, body.parent_id))


@router.post("/{topic_id}/merge", response_model=TopicOut)
def merge_topic(topic_id: uuid.UUID, body: TopicMerge, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return topic_out(topics.merge_topic(db, scope, topic_id, body.target_id))


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    topics.delete_topic(db, scope, topic_id)
    return Response(status_code=204)
