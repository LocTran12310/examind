"""Knowledge tree editing on ltree paths (ADR-04, AC-21, AC-22, A-10, A-13)."""
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found, validation
from app.deps import OrgScope
from app.models import Subject, Topic
from app.models.taxonomy import LEVEL_KINDS, MAX_TOPIC_DEPTH, topic_label
from app.services import audit

# Hooks later features register to repoint/guard references (e.g. question_topics).
REFERENCE_COUNTERS: list = []   # fn(db, org_id, topic_ids) -> int
REFERENCE_MOVERS: list = []     # fn(db, org_id, from_id, to_id) -> None


def default_kind(depth: int) -> str:
    return LEVEL_KINDS[min(depth, len(LEVEL_KINDS)) - 1]


def get_topic(db: Session, scope: OrgScope, topic_id) -> Topic:
    t = db.get(Topic, topic_id)
    if t is None or t.organization_id != scope.org_id:
        raise not_found("Không tìm thấy chuyên đề")
    return t


def list_topics(db: Session, scope: OrgScope, subject_id=None):
    stmt = select(Topic).where(Topic.organization_id == scope.org_id)
    if subject_id:
        stmt = stmt.where(Topic.subject_id == subject_id)
    topics = db.scalars(stmt.order_by(Topic.path)).all()
    children: dict = {}
    for t in topics:
        if t.parent_id:
            children[t.parent_id] = children.get(t.parent_id, 0) + 1
    return topics, children


def depth_of(path: str) -> int:
    return path.count(".") + 1


def create_topic(db: Session, scope: OrgScope, subject_id, name: str, parent_id=None, level_kind=None, grade=None) -> Topic:
    if not (name or "").strip():
        raise validation("Tên chuyên đề không được để trống", "name")
    parent = get_topic(db, scope, parent_id) if parent_id else None
    if parent:
        subject_id = parent.subject_id
    subject = db.get(Subject, subject_id) if subject_id else None
    if subject is None or subject.organization_id != scope.org_id:
        raise validation("Môn học không hợp lệ", "subject_id")
    depth = depth_of(parent.path) + 1 if parent else 1
    if depth > MAX_TOPIC_DEPTH:
        raise validation(f"Cây chuyên đề tối đa {MAX_TOPIC_DEPTH} cấp", "parent_id")
    kind = level_kind or default_kind(depth)
    if kind not in LEVEL_KINDS:
        raise validation("Loại cấp không hợp lệ", "level_kind")
    tid = uuid.uuid4()
    path = f"{parent.path}.{topic_label(tid)}" if parent else topic_label(tid)
    sort = db.scalar(select(func.coalesce(func.max(Topic.sort), -1) + 1).where(Topic.organization_id == scope.org_id, Topic.parent_id == (parent.id if parent else None)))
    t = Topic(id=tid, organization_id=scope.org_id, subject_id=subject.id, parent_id=parent.id if parent else None,
              name=name.strip(), level_kind=kind, grade=grade if grade is not None else (parent.grade if parent else None), path=path, sort=sort or 0)
    db.add(t)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "topic.create", "topic", t.id, name=t.name)
    return t


def update_topic(db: Session, scope: OrgScope, topic_id, name=None, level_kind=None, grade=None, sort=None) -> Topic:
    t = get_topic(db, scope, topic_id)
    if name is not None:
        if not name.strip():
            raise validation("Tên chuyên đề không được để trống", "name")
        t.name = name.strip()
    if level_kind is not None:
        if level_kind not in LEVEL_KINDS:
            raise validation("Loại cấp không hợp lệ", "level_kind")
        t.level_kind = level_kind
    if grade is not None:
        t.grade = grade or None
    if sort is not None:
        t.sort = sort
    return t


def _subtree_depth(db: Session, t: Topic) -> int:
    return db.execute(text("select max(nlevel(path)) - nlevel(cast(:p as ltree)) from topics where organization_id=:o and path <@ cast(:p as ltree)"),
                      {"p": t.path, "o": t.organization_id}).scalar() or 0


def move_topic(db: Session, scope: OrgScope, topic_id, new_parent_id) -> Topic:
    t = get_topic(db, scope, topic_id)
    parent = get_topic(db, scope, new_parent_id) if new_parent_id else None
    if parent:
        if parent.id == t.id or parent.path == t.path or parent.path.startswith(t.path + "."):
            raise AppError("invalid_move", "Không thể chuyển chuyên đề vào chính nó hoặc nhánh con của nó", 409)
        if parent.subject_id != t.subject_id:
            raise AppError("invalid_move", "Chỉ di chuyển trong cùng một môn", 409)
    new_path = f"{parent.path}.{topic_label(t.id)}" if parent else topic_label(t.id)
    if depth_of(new_path) + _subtree_depth(db, t) > MAX_TOPIC_DEPTH:
        raise AppError("invalid_move", f"Cây chuyên đề tối đa {MAX_TOPIC_DEPTH} cấp", 409)
    old_path = t.path
    db.execute(
        text("""update topics
                   set path = case when path = cast(:old as ltree) then cast(:new as ltree)
                                    else cast(:new as ltree) || subpath(path, nlevel(cast(:old as ltree))) end
                 where organization_id = :o and path <@ cast(:old as ltree)"""),
        {"new": new_path, "old": old_path, "o": scope.org_id},
    )
    t.parent_id = parent.id if parent else None
    db.flush()
    db.expire_all()  # the bulk path rewrite bypassed the identity map
    audit.record(db, scope.user, scope.org_id, "topic.move", "topic", t.id, to=str(parent.id) if parent else None)
    return t


def _reference_count(db: Session, org_id, topic_ids) -> int:
    return sum(fn(db, org_id, topic_ids) for fn in REFERENCE_COUNTERS)


def delete_topic(db: Session, scope: OrgScope, topic_id) -> None:
    t = get_topic(db, scope, topic_id)
    if db.scalar(select(Topic.id).where(Topic.parent_id == t.id).limit(1)):
        raise AppError("topic_has_children", "Chuyên đề còn nhánh con — hãy xóa hoặc gộp nhánh con trước", 409)
    if _reference_count(db, scope.org_id, [t.id]):
        raise AppError("topic_in_use", "Chuyên đề đang được gắn cho câu hỏi — hãy gộp vào chuyên đề khác", 409)
    db.delete(t)
    audit.record(db, scope.user, scope.org_id, "topic.delete", "topic", t.id, name=t.name)


def merge_topic(db: Session, scope: OrgScope, topic_id, target_id) -> Topic:
    src = get_topic(db, scope, topic_id)
    target = get_topic(db, scope, target_id)
    if target.id == src.id or target.path.startswith(src.path + "."):
        raise AppError("invalid_move", "Không thể gộp vào chính nó hoặc nhánh con của nó", 409)
    if target.subject_id != src.subject_id:
        raise AppError("invalid_move", "Chỉ gộp trong cùng một môn", 409)
    for child in db.scalars(select(Topic).where(Topic.parent_id == src.id).order_by(Topic.sort)).all():
        move_topic(db, scope, child.id, target.id)
    for fn in REFERENCE_MOVERS:
        fn(db, scope.org_id, src.id, target.id)
    db.delete(src)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "topic.merge", "topic", target.id, merged=str(src.id), name=src.name)
    return target
