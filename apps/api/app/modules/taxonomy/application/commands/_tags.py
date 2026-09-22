import uuid

from app.modules.taxonomy.domain.entities import Tag
from app.modules.taxonomy.domain.ports import SubjectLookup, TagRepository
from app.shared.domain.errors import Conflict, Invalid, NotFound


def load_tag(tags: TagRepository, org_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
    tag = tags.get(org_id, tag_id)
    if tag is None:
        raise NotFound("Không tìm thấy tag")
    return tag


def ensure_unique(tags: TagRepository, tag: Tag) -> None:
    if tags.name_taken(tag.organization_id, tag.group, tag.name, exclude_id=tag.id):
        raise Conflict("Tag đã tồn tại trong nhóm này", "name")


def ensure_subject(subjects: SubjectLookup, org_id: uuid.UUID, subject_id: uuid.UUID | None) -> None:
    if subject_id is not None and not subjects.exists(org_id, subject_id):
        raise Invalid("Môn học không hợp lệ", "subject_id")
