---
feature: bulk-safety
adrs: 4
---

# Logical design

## Approach

The data for an undo almost exists. Every command in the bank already calls
`record(log, actor, q, action, before, after)`, which appends a row to `review_events` with a JSONB snapshot on
each side. Two things are missing and both are small:

1. **The snapshot is too narrow.** `Question.snapshot()` returns `status, answer, confidence, issues` — none of
   the five fields the bulk bar changes. It widens to cover difficulty, grade, subject, the topic list with its
   primary, and the tag ids. A wider snapshot costs a few hundred bytes per event and makes the history
   readable as well as restorable.
2. **Nothing groups the rows, and nothing reads them.** One bulk edit over 20 questions is 20 rows that only a
   timestamp ties together. A `batch_id` column makes it one unit; two queries and one command make it visible
   and reversible.

So the feature is: widen the snapshot, group the events, read them back, restore one group. The bank's screens
gain a panel and a toast button; nothing else about the bulk bar changes.

### Restoring

`UndoBatch` loads every event of the batch, takes each event's `before`, and writes the fields back through the
same aggregate and the same guards a manual edit goes through — a restore that skipped the guards could put a
question in another subject's tree, which is exactly the state `subject_topic_conflict` exists to prevent. If any
question of the batch is gone, or any guard refuses, nothing is written (AC-02). The restore appends its own
events under a new batch, with `action: "undo"` and `undone_batch_id` pointing at the original (AC-04).

### Reading

`POST /question-events/search` returns one row per batch: `batch_id`, `created_at`, actor name, `action`, the
field names that changed, the number of questions, and `undoable` with a reason when it is false — too old
(ADR-02), already undone, or itself an undo. The bank gets a "Thay đổi gần đây" sheet over this; the toast's
"Hoàn tác" is the same command with the batch the mutation just returned.

## Alternatives considered

- **An `undo` table of its own.** `review_events` is already the append-only history of the bank and already
  carries before/after. A second table would have to be kept in step with it, and the first time they disagreed
  the history would be the thing nobody trusts.
- **A three-way merge on undo** (restore only the fields nobody touched since). It is the technically nicer
  answer and the wrong product answer: the teacher pressing "Hoàn tác" wants the state they remember, not a
  state neither version ever had. The refusal in AC-02 and the note in the row cover the case honestly.
- **A confirmation dialog on every bulk action.** It is the obvious fix and it makes the fast path — the one
  Loc Tran likes — slow for the 99 times the click was right, while still not helping the mistake found an hour
  later. Undo beats confirm when the action is cheap to reverse.
- **A soft-delete undo for "Xóa".** Out of scope: deletion already asks for confirmation, and a question
  referenced by an exam cannot be deleted at all.

## Failure modes

| Code | HTTP | When | Details |
| --- | --- | --- | --- |
| `batch_not_found` | 404 | No such batch in this organisation | — |
| `batch_expired` | 422 | Older than the undo window | `fields.batch_id`, `fields.age_days` |
| `batch_already_undone` | 409 | The batch was already restored | `fields.undone_by` |
| `questions_gone` | 422 | A question of the batch no longer exists | `fields.question_ids` |
| `subject_topic_conflict` | 422 | Restoring a subject would leave a question in another subject's tree | as today |

## ADRs

### ADR-01 — The batch is a column on `review_events`, not a new table
**Status:** accepted
A nullable `batch_id UUID` plus an index on `(organization_id, batch_id)` and on `(organization_id, created_at)`.
Every command that writes more than one event in one request generates one id and passes it down; a single edit
gets its own batch of one, so the history has one shape. Rows written before this migration have `batch_id NULL`
and are read as "one event, not undoable" — no backfill, because a batch cannot be reconstructed from a
timestamp with any confidence.

### ADR-02 — The undo window is 7 days
**Status:** accepted
Long enough for "I noticed on Monday what I did on Friday", short enough that an undo never silently reverses
work a whole class has since been assessed on. It is a constant in the domain, not a setting: a second knob
nobody tunes is a second thing to explain. A batch outside the window still shows in the list with its reason.

### ADR-03 — Questions carry no default points; points stay on the paper
**Status:** accepted
Loc Tran asked whether each question should have a default score. The answer is no, and it is worth writing
down because the opposite looks sensible:

- The same question is worth different amounts in different papers — 0,25 in a 40-question paper on the 10-point
  scale, 1,0 in a 15-minute quiz of ten questions. A number on the question would be right in one paper and
  wrong in the next.
- The paper already answers it: `settings.points_by_type` gives every question of a type its default the moment
  it enters the exam, one input per part changes all of them, and a single question can still be overridden. The
  weighting strip states the raw total and the scale.
- Two defaults — one on the question, one on the paper — is a conflict that has to be resolved on every insert,
  and whichever wins, the other is a number on screen that does nothing.

What *is* worth having, and is already there, is the per-part default plus the per-question override. If a
recurring paper shape needs its own numbers, the place for that is an exam template, not the bank.

### ADR-04 — Undo goes through the aggregate and its guards
**Status:** accepted
A restore writes with the same commands and checks as an edit. It is slower than a column-wise `UPDATE` and it
is the only version that cannot put the bank into a state the product refuses to create.
