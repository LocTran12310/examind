"""Exam builder rules: settings, sections and numbering, blueprint rows, the order of a document's questions
(exam-practice US-01, A-01, A-04; official-exam-ingestion AC-11)."""
import uuid

from app.modules.assessment.domain.entities import DEFAULT_POINTS, SECTION_OF_TYPE, SECTION_ORDER, ExamQuestion
from app.modules.assessment.domain.value_objects import PoolFilter
from app.shared.domain.errors import Invalid

MAX_ROW_COUNT = 200


def normalized_settings(settings: dict | None) -> dict:
    """Points per question type (> 0) and the scale; unknown types are ignored."""
    s = {"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10}
    if settings:
        for k, v in (settings.get("points_by_type") or {}).items():
            if k in DEFAULT_POINTS:
                if not isinstance(v, (int, float)) or v <= 0:
                    raise Invalid("Điểm phải lớn hơn 0", "settings")
                s["points_by_type"][k] = float(v)
        if settings.get("scale_to"):
            s["scale_to"] = float(settings["scale_to"])
    return s


def merged_settings(old: dict | None, changes: dict) -> dict:
    """A settings patch: points per type are merged into the old ones."""
    old = old or {}
    return normalized_settings({**old, **changes,
                                "points_by_type": {**old.get("points_by_type", {}), **(changes.get("points_by_type") or {})}})


def title_of(title: str | None) -> str:
    if not (title or "").strip():
        raise Invalid("Nhập tên đề", "title")
    return title.strip()


def section_of(qtype: str) -> str:
    return SECTION_OF_TYPE.get(qtype, "I")


def renumbered(rows: list[ExamQuestion]) -> None:
    """Positions 1..n: sections I → IV, the current order inside each."""
    ordered = sorted(rows, key=lambda r: (SECTION_ORDER.index(r.section) if r.section in SECTION_ORDER else 9, r.position))
    for i, eq in enumerate(ordered, start=1):
        eq.position = i


def check_points(points) -> float:
    if not isinstance(points, (int, float)) or points <= 0:
        raise Invalid("Điểm phải lớn hơn 0", "points")
    return float(points)


def check_rows(rows: list[dict]) -> None:
    for i, r in enumerate(rows):
        if not isinstance(r.get("count"), int) or not 1 <= r["count"] <= MAX_ROW_COUNT:
            raise Invalid(f"Dòng {i + 1}: số câu từ 1 đến 200", "rows")
        if not (r.get("topic_id") or r.get("tag_id")):
            raise Invalid(f"Dòng {i + 1}: chọn chuyên đề hoặc tag", "rows")


def _uuid(value, message: str, field: str) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except ValueError:
        raise Invalid(message, field) from None


def row_filter(subject_id: uuid.UUID | None, row: dict) -> PoolFilter:
    """The usable questions a blueprint row draws from (in the exam's subject when it has one)."""
    return PoolFilter(subject_id=subject_id, type=row.get("type") or None, difficulty=row.get("difficulty") or None,
                      topic_id=_uuid(row.get("topic_id"), "Chuyên đề không hợp lệ", "topic_ids"),
                      tag_id=_uuid(row.get("tag_id"), "Tag không hợp lệ", "tag_ids"))


def swap_filter(subject_id: uuid.UUID | None, blueprint: list, row: int | None, qtype: str) -> PoolFilter:
    """A swap draws from the question's blueprint row, or else from the same type in the exam's subject."""
    if row is not None:
        spec = blueprint[row] if row < len(blueprint or []) else {"type": qtype}
        return row_filter(subject_id, spec)
    return PoolFilter(subject_id=subject_id, type=qtype)


def part_key(part: str | None, number: int | None) -> tuple:
    """PHẦN then Câu: numeric parts in order, others after."""
    part = part or ""
    return (int(part) if part.isdigit() else 99, part, number or 0)


def document_title(meta: dict, filename: str, title: str | None) -> str:
    default = " · ".join(x for x in (meta.get("source_name"), meta.get("exam_kind"), meta.get("school_year")) if x)
    stem = filename.rsplit(".", 1)[0]
    return (title or default or stem)[:200]
