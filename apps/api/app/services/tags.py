import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import conflict, not_found, validation
from app.deps import OrgScope
from app.services.paging import Col, ListParams, paginate
from app.models import Subject, Tag
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


TAG_COLS = {"group": Col(Tag.group, "exact"), "name": Col(Tag.name)}


def _subject(db: Session, scope: OrgScope, group: str, subject_id) -> uuid.UUID | None:
    if subject_id is None or group == "source":  # nguồn đề is shared by every subject
        return None
    s = db.get(Subject, subject_id)
    if s is None or s.organization_id != scope.org_id:
        raise validation("Môn học không hợp lệ", "subject_id")
    return s.id


def list_tags(db: Session, scope: OrgScope, params: ListParams, subject_id: str | None = None, include_shared: bool = True):
    """`subject_id`: that subject's tags plus shared ones (pickers); "shared" = shared only;
    `include_shared=false` = exactly that subject (the Tags page filter)."""
    stmt = select(Tag).where(Tag.organization_id == scope.org_id)
    if subject_id == "shared":
        stmt = stmt.where(Tag.subject_id.is_(None))
    elif subject_id:
        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            raise validation("Môn học không hợp lệ", "subject_id")
        stmt = stmt.where(or_(Tag.subject_id == sid, Tag.subject_id.is_(None)) if include_shared else Tag.subject_id == sid)
    return paginate(db, stmt, params, TAG_COLS, search=[Tag.name], default_sort=[Tag.group, func.lower(Tag.name), Tag.id])


def create_tag(db: Session, scope: OrgScope, group: str, name: str, subject_id=None) -> Tag:
    tag = Tag(organization_id=scope.org_id, group=group, name=_check(db, scope, group, name), subject_id=_subject(db, scope, group, subject_id))
    db.add(tag)
    db.flush()
    return tag


UNSET = object()


def update_tag(db: Session, scope: OrgScope, tag_id, group: str | None, name: str | None, subject_id=UNSET) -> Tag:
    tag = get_tag(db, scope, tag_id)
    group = group or tag.group
    tag.name = _check(db, scope, group, name if name is not None else tag.name, exclude_id=tag.id)
    tag.group = group
    if subject_id is not UNSET or group == "source":
        tag.subject_id = _subject(db, scope, group, None if subject_id is UNSET else subject_id)
    return tag


def delete_tag(db: Session, scope: OrgScope, tag_id) -> None:
    tag = get_tag(db, scope, tag_id)
    for fn in TAG_REFERENCE_DELETERS:
        fn(db, scope.org_id, tag.id)
    db.delete(tag)
