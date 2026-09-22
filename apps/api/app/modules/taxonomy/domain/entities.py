from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Invalid
from app.shared.domain.ids import new_id

TAG_GROUPS = ("method", "skill", "source", "custom")
SHARED_GROUPS = ("source",)  # nguồn đề belongs to every subject


def clean_tag_name(name: str | None) -> str:
    name = (name or "").strip()
    if not name:
        raise Invalid("Tên tag không được để trống", "name")
    if len(name) > 100:
        raise Invalid("Tên tag tối đa 100 ký tự", "name")
    return name


def check_group(group: str) -> str:
    if group not in TAG_GROUPS:
        raise Invalid("Nhóm tag không hợp lệ", "group")
    return group


@dataclass(eq=False)
class Tag:
    organization_id: uuid.UUID
    group: str
    name: str
    subject_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utcnow)

    @classmethod
    def create(cls, organization_id: uuid.UUID, group: str, name: str, subject_id: uuid.UUID | None = None) -> "Tag":
        group = check_group(group)
        return cls(organization_id=organization_id, group=group, name=clean_tag_name(name),
                   subject_id=None if group in SHARED_GROUPS else subject_id)

    def change(self, group: str | None = None, name: str | None = None) -> None:
        self.group = check_group(group or self.group)
        self.name = clean_tag_name(self.name if name is None else name)
        if self.group in SHARED_GROUPS:
            self.subject_id = None

    def assign_subject(self, subject_id: uuid.UUID | None) -> None:
        self.subject_id = None if self.group in SHARED_GROUPS else subject_id
