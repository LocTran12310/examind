"""The knowledge tree (ADR-04, AC-21, AC-22, A-10, A-13): a topic's `path` is the chain of its ancestors'
stable labels, so a rename never touches it and a move rewrites one subtree."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.errors import Conflict, Invalid, NotFound
from app.shared.domain.ids import new_id

LEVEL_KINDS = ("strand", "topic", "subtopic", "type")
MAX_TOPIC_DEPTH = 5


def topic_label(topic_id: uuid.UUID) -> str:
    """ltree label for a topic: stable across renames (ADR-04)."""
    return "t" + topic_id.hex[:12]


def depth_of(path: str) -> int:
    return path.count(".") + 1


def default_kind(depth: int) -> str:
    return LEVEL_KINDS[min(depth, len(LEVEL_KINDS)) - 1]


def clean_topic_name(name: str | None) -> str:
    if not (name or "").strip():
        raise Invalid("Tên chuyên đề không được để trống", "name")
    return name.strip()


def check_kind(kind: str) -> str:
    if kind not in LEVEL_KINDS:
        raise Invalid("Loại cấp không hợp lệ", "level_kind")
    return kind


def invalid_move(message: str) -> Conflict:
    return Conflict(message, code="invalid_move")


@dataclass(eq=False)
class Topic:
    organization_id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    level_kind: str
    path: str
    parent_id: uuid.UUID | None = None
    grade: int | None = None
    sort: int = 0
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def depth(self) -> int:
        return depth_of(self.path)

    @classmethod
    def create(cls, organization_id: uuid.UUID, subject_id: uuid.UUID, name: str, parent: "Topic | None" = None,
               level_kind: str | None = None, grade: int | None = None, sort: int = 0) -> "Topic":
        """A new node under `parent` (same subject), or a new strand; checks depth and kind."""
        tid = new_id()
        depth = parent.depth + 1 if parent else 1
        if depth > MAX_TOPIC_DEPTH:
            raise Invalid(f"Cây chuyên đề tối đa {MAX_TOPIC_DEPTH} cấp", "parent_id")
        return cls(id=tid, organization_id=organization_id, subject_id=parent.subject_id if parent else subject_id,
                   parent_id=parent.id if parent else None, name=clean_topic_name(name),
                   level_kind=check_kind(level_kind or default_kind(depth)),
                   grade=grade if grade is not None else (parent.grade if parent else None),
                   path=f"{parent.path}.{topic_label(tid)}" if parent else topic_label(tid), sort=sort)

    def change(self, name: str | None = None, level_kind: str | None = None, grade: int | None = None, sort: int | None = None) -> None:
        if name is not None:
            self.name = clean_topic_name(name)
        if level_kind is not None:
            self.level_kind = check_kind(level_kind)
        if grade is not None:
            self.grade = grade or None
        if sort is not None:
            self.sort = sort

    def contains(self, other: "Topic") -> bool:
        """`other` is this node or one of its descendants."""
        return other.id == self.id or other.path == self.path or other.path.startswith(self.path + ".")

    def path_under(self, parent: "Topic | None", subtree_depth: int) -> str:
        """The new path of this node moved under `parent` (None = root); `subtree_depth` = levels below it."""
        if parent is not None:
            if self.contains(parent):
                raise invalid_move("Không thể chuyển chuyên đề vào chính nó hoặc nhánh con của nó")
            if parent.subject_id != self.subject_id:
                raise invalid_move("Chỉ di chuyển trong cùng một môn")
        path = f"{parent.path}.{topic_label(self.id)}" if parent else topic_label(self.id)
        if depth_of(path) + subtree_depth > MAX_TOPIC_DEPTH:
            raise invalid_move(f"Cây chuyên đề tối đa {MAX_TOPIC_DEPTH} cấp")
        return path

    def check_merge_into(self, target: "Topic") -> None:
        if target.id == self.id or target.path.startswith(self.path + "."):
            raise invalid_move("Không thể gộp vào chính nó hoặc nhánh con của nó")
        if target.subject_id != self.subject_id:
            raise invalid_move("Chỉ gộp trong cùng một môn")


def topic_not_found() -> NotFound:
    return NotFound("Không tìm thấy chuyên đề")
