from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import conflict, not_found, validation
from app.deps import OrgScope
from app.models import Tag
from app.models.taxonomy import TAG_GROUPS

TAG_REFERENCE_DELETERS: list = []  # fn(db, org_id, tag_id) — later features drop question_tags rows


def _check(db: Session, scope: OrgScope, group: str, name: str, exclude_id=None) -> str:
    if group not in TAG_GROUPS:
        raise validation("Nhóm tag không hợp lệ", "group")
    name = (name or "").strip()
    if not name:
        raise validation("Tên tag không được để trống", "name")
    stmt = select(Tag.id).where(Tag.organization_id == scope.org_id, Tag.group == group, func.lower(Tag.name) == name.lower())
    if exclude_id:
        stmt = stmt.where(Tag.id != exclude_id)
    if db.scalar(stmt):
        raise conflict("Tag đã tồn tại trong nhóm này", "name")
    return name


def get_tag(db: Session, scope: OrgScope, tag_id) -> Tag:
    t = db.get(Tag, tag_id)
    if t is None or t.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tag")
    return t


def list_tags(db: Session, scope: OrgScope, group: str | None = None):
    stmt = select(Tag).where(Tag.organization_id == scope.org_id)
    if group:
        stmt = stmt.where(Tag.group == group)
    return db.scalars(stmt.order_by(Tag.group, func.lower(Tag.name))).all()


def create_tag(db: Session, scope: OrgScope, group: str, name: str) -> Tag:
    tag = Tag(organization_id=scope.org_id, group=group, name=_check(db, scope, group, name))
    db.add(tag)
    db.flush()
    return tag


def update_tag(db: Session, scope: OrgScope, tag_id, group: str | None, name: str | None) -> Tag:
    tag = get_tag(db, scope, tag_id)
    group = group or tag.group
    tag.name = _check(db, scope, group, name if name is not None else tag.name, exclude_id=tag.id)
    tag.group = group
    return tag


def delete_tag(db: Session, scope: OrgScope, tag_id) -> None:
    tag = get_tag(db, scope, tag_id)
    for fn in TAG_REFERENCE_DELETERS:
        fn(db, scope.org_id, tag.id)
    db.delete(tag)
