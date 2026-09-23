"""Reading the review history back: what a recorded change moved, what names a batch of events, whether that batch
can still be taken back, and the state its questions have to go back to (bulk-safety ADR-01, ADR-02, ADR-04)."""
from collections.abc import Iterable
from datetime import datetime, timedelta
import uuid

from app.modules.bank.domain.entities import SNAPSHOT_FIELDS, ReviewEvent

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


def restore_targets(events: Iterable[ReviewEvent]) -> dict[uuid.UUID, dict]:
    """The state each question of a batch has to go back to: the `before` of its events merged field by field (AC-01).

    A snapshot is partial — one event of a request records the placement, another the tags, a third the columns it
    moved — so the target is their union, and a key no event mentions is left out rather than guessed. Where two
    events name the same field, the value to keep is the one the question held when the request started. The events
    of one request share a timestamp, so their order in the table decides nothing; the earliest value is instead the
    one no event of the batch produced, since a `before` that appears as another event's `after` is something this
    same request wrote (the tagging queue placing one question twice is the case that makes them differ)."""
    befores: dict[tuple[uuid.UUID, str], list] = {}
    afters: dict[tuple[uuid.UUID, str], list] = {}
    for e in events:
        if e.question_id is None:
            continue
        for snap, seen in ((e.before, befores), (e.after, afters)):
            for f in SNAPSHOT_FIELDS:
                if snap and f in snap:
                    seen.setdefault((e.question_id, f), []).append(snap[f])
    targets: dict[uuid.UUID, dict] = {}
    for (question_id, f), values in befores.items():
        made = afters.get((question_id, f), ())
        targets.setdefault(question_id, {})[f] = next((v for v in values if v not in made), values[0])
    return targets


def lost_question(e: ReviewEvent) -> bool:
    """Whether this event is what a deleted question left behind. `review_events.question_id` is ON DELETE SET NULL,
    so deleting a question empties the link without touching the row: an event that records a question's state but
    names no question is one the batch can no longer put back, and the history cannot even say which one it was. A
    batch's own summary line says something else — a count, a document, a threshold — and is not one of these."""
    before, after = e.before or {}, e.after or {}
    return e.question_id is None and any(f in before for f in SNAPSHOT_FIELDS) and not set(after) - set(SNAPSHOT_FIELDS)


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
