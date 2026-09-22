from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class TagView:
    id: uuid.UUID
    group: str
    name: str
    subject_id: uuid.UUID | None


def tag_view(t) -> TagView:
    return TagView(id=t.id, group=t.group, name=t.name, subject_id=t.subject_id)
