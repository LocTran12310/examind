"""Reading the review history back: what a recorded change moved, what names a batch of events, and whether that
batch can still be taken back (bulk-safety ADR-01, ADR-02)."""
from datetime import datetime, timedelta

from app.modules.bank.domain.entities import SNAPSHOT_FIELDS

UNDO_WINDOW = timedelta(days=7)  # ADR-02: long enough for "I noticed on Monday", short enough not to reverse a month
UNDONE_BATCH = "undone_batch_id"  # an `undo` event names the batch it reversed under this key of its `after`
# what names a batch of events, coarsest first: an undo, then the bulk bar, then the verb of a single edit
BATCH_ACTIONS = ("undo", "bulk", "triage", "edit", "answer", "approve", "reject", "restore", "spot_fail", "spot_ok",
                 "topic", "tag", "skip")
BLOCKED = {
    "no_batch": "Thay đổi được ghi trước khi có hoàn tác",
    "is_undo": "Đây đã là một lần hoàn tác",
    "already_undone": "Lượt sửa này đã được hoàn tác",
    "expired": f"Quá {UNDO_WINDOW.days} ngày nên không hoàn tác được",
}


def changed_fields(before: dict | None, after: dict | None) -> list[str]:
    """The snapshot fields one event moved, in snapshot order. A field missing on either side is unknown, not empty:
    an event recorded before the snapshot widened says nothing about the difficulty, so it never claims it changed."""
    b, a = before or {}, after or {}
    return [f for f in SNAPSHOT_FIELDS if f in b and f in a and b[f] != a[f]]


def batch_action(actions) -> str:
    """One name for a batch that wrote several kinds of event — a bulk edit also places topics and tags."""
    seen = set(actions)
    return next((a for a in BATCH_ACTIONS if a in seen), next(iter(sorted(seen)), ""))


def undo_block(has_batch: bool, action: str, created_at: datetime | None, now: datetime, already_undone: bool) -> str | None:
    """Why this batch can no longer be taken back, or None when it still can (AC-05). Order matters: the most
    specific answer wins, so a batch that was undone says so rather than blaming its age."""
    if not has_batch:
        return "no_batch"
    if action == "undo":
        return "is_undo"
    if already_undone:
        return "already_undone"
    if created_at is not None and now - created_at > UNDO_WINDOW:
        return "expired"
    return None
