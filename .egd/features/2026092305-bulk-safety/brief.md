# A bulk edit you can take back, and a way back out of a page

## Problem
Loc Tran, walking the bank and the assignment report (chat, 2026-09-23, with screenshots):
- The bank's toolbar sets mức độ, môn, lớp, chuyên đề and tags on the selection in one click. It is fast, and
  that is the danger: one wrong item on a dropdown changes every selected question, with nothing but a toast.
- After the change there is no way back. Worse, there is no way to **find** it: `review_events` records a
  before/after snapshot for every question a bulk edit touches, but the snapshot holds only
  `status, answer, confidence, issues` — not difficulty, grade, subject, topic or tags. The five things the
  toolbar can change are exactly the five the history does not keep, and nothing in the product reads that
  table back anyway.
- The selection count sits at the far right of the toolbar, away from the buttons that act on it.
- The assignment report (`/org/assignments/<id>`) has no way back to where the teacher came from. The same is
  true of the attempt result, the new-question form and the question preview.

## Outcome
---
feature: bulk-safety
slug: 2026092305-bulk-safety
owner: Loc Tran
created: 2026-09-23
status: approved
---

## Success signal
A teacher sets "Lớp 12" on two questions by mistake, presses "Hoàn tác" in the toast, and the two questions are
exactly as they were. A teacher who notices the mistake an hour later opens "Thay đổi gần đây", sees who changed
what and when, and undoes that one batch.

## Out of scope
- A general undo stack for every screen; this is the bank's bulk bar and nothing else
- Undoing a delete (a deleted question is gone; the confirm dialog stays the guard there)
- Per-question default points in the bank — see ADR-03 for why the answer is no
- Changing what the toolbar can set

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher curating the bank | A misclick changes N questions silently and irreversibly | The change can be undone from the toast, and found and undone later from a list of recent changes |
| Teacher curating the bank | "Đã chọn 2" is far from the buttons | Each bulk action names how many questions it is about to change |
| Teacher reading a report | Browser back only | A back link, like every other detail page |

## Constraints
| Kind | Detail |
| --- | --- |
| Contract | Lists stay on the search contract; undo is a command, not a PATCH |
| UI | shadcn only; the toolbar keeps its shape |
| Data | One migration: a batch id on `review_events`, and a wider snapshot |
| History | `review_events` stays append-only — an undo is a new event, never a deletion |
