---
feature: history-keeps-ids
adrs: 2
---

# Logical design

## Approach

`review_events.question_id` is declared
`ForeignKey("questions.id", ondelete="SET NULL")`. The constraint is what empties the column; the column itself
is fine. So the change is to drop the constraint and keep everything else — the column, its index, its type.
After that a deletion touches no row of `review_events`, and the id stays readable whether or not the question
still exists.

Two pieces of code then stop needing to guess:

- `lost_question(event)` exists because an event that records a question's state while naming no question is one
  the batch can no longer restore. It stays, because rows nulled before this migration still look like that, and
  its docstring says so — but from now on nothing new enters that state.
- The `questions_gone` refusal already computes `gone` (ids in the batch that the repository cannot load) and
  puts them in `details.fields.question_ids`. With the ids preserved, that list is now complete instead of
  being empty in exactly the case it was written for.

## Alternatives considered

- **A second column** (`question_ref`) beside the foreign-keyed one. Two columns holding the same id are two
  columns that will disagree — the first time something writes one and not the other, and there is no way to
  tell afterwards which one was right.
- **`ON DELETE RESTRICT`.** It keeps the id by refusing the deletion, which makes the history a reason a teacher
  cannot delete a question. The history must not take the product hostage.
- **Copying the question into the event** (stem, options) so a deleted one can be described. That is an archive,
  not a reference, and it changes what a snapshot means. Out of scope in the intent.

## Failure modes

Unchanged. `questions_gone` (422) keeps its code and its shape; only `fields.question_ids` stops being empty in
the deleted case, and the message names the count it already knew.

## ADRs

### ADR-01 — An audit log holds ids, not foreign keys
**Status:** accepted
`review_events` records what happened to a question at a moment. That record must outlive the question, so the
column is a plain `UUID` with its index and no constraint. Referential integrity is the right default for data
that describes the present and the wrong one for data that describes the past. The other history tables are
worth reading the same way later; this migration changes only this one, because this is the one that lost data.

### ADR-02 — The downgrade states what it costs
**Status:** accepted
Re-creating the constraint requires every value in the column to exist in `questions`, so the downgrade nulls
the ids of questions that are gone before it adds the foreign key back. That is the data this feature exists to
keep, so the docstring says plainly that the downgrade loses it. The upgrade itself is loss-free and needs no
backfill.
