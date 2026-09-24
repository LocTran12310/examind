---
feature: history-keeps-ids
slug: 2026092401-history-keeps-ids
owner: Loc Tran
created: 2026-09-24
status: approved
---

# Intent — The history keeps the id of the question it is about

## Problem
Closing F18 left one limit on the record, and Loc Tran asked for it (chat, 2026-09-24):
`review_events.question_id` carries a foreign key with `ON DELETE SET NULL`, so deleting a question empties the
link in every event that question ever left behind. The row survives with its before/after snapshot and no
longer says whose snapshot it is.

Two consequences today:
- A batch that lost a question is refused whole, correctly, but cannot name which one — it says "một số câu"
  because there is nothing left to name.
- The history of a deleted question becomes anonymous: rows that read "1 câu" with no way to tell which.

A history that forgets what it is about is not a history. An audit log is precisely the place where a reference
should outlive the thing it refers to.

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher undoing a batch | "Một số câu … đã bị xóa" | The refusal names the questions it can no longer restore |
| Whoever reads the record later | An event with no subject | Every event still says which question it was about |

## Success signal
Deleting a question no longer changes a single row of `review_events`, and an undo blocked by that deletion
names the ids it could not put back.

## Out of scope
- Keeping a copy of the deleted question itself (its stem, its options) — this is a reference, not an archive
- Restoring a deleted question; deletion stays final and stays behind its confirmation
- Backfilling ids that are already lost: the rows nulled before this migration cannot be recovered

## Constraints
| Kind | Detail |
| --- | --- |
| Data | One migration; `review_events` stays append-only and keeps its index on `question_id` |
| Behaviour | An undo that cannot restore a batch still refuses the whole batch |
| History | No row is rewritten, and no event is deleted |
