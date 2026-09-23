---
feature: review-ux
adr_count: 3
---

# Logical design

## Approach
Three slices: the list says one thing per document, the document page shows every question with a filter and lets
a decision be taken back, and the exam screen states its own weighting.

- **bank / read model**: the review list gains `review_state` (`pending` / `in_progress` / `done`) derived from the
  counts it already computes, as an ordinary filterable and sortable column of `POST /review/documents/search`,
  plus `pending` (how many questions still wait). The badges stay, but behind the state, not instead of it.
- **bank / document queue**: `GET|POST /review/documents/{id}/questions` answers the document's questions with a
  `state` filter (`pending` default, `approved`, `rejected`, `duplicate`, `all`) and paging, so the page can show
  what was decided, not only what is waiting. The existing keyboard queue keeps working on the `pending` filter.
- **bank / re-decide**: no new endpoint — the existing question update and `POST /questions/bulk` already move
  `status`; the page calls them and invalidates the document's counts.
- **web / review list**: one state chip + "còn N câu", the detail counts in a popover, a state filter in the column
  header, and the sample renamed with its explanation.
- **web / review document**: a state filter above the queue; a row names its state; the action buttons say what
  they do; editing opens the existing `QuestionForm`, for any state.
- **web / exam**: a weighting strip on the exam screen — points per part, the raw total, and what it becomes on the
  10-point scale — next to the per-question points that already exist.

## Alternatives rejected
| Option | Why not |
| --- | --- |
| Keep every badge and add a filter per badge | Six filters for one question ("is there work left?") |
| A separate "đã duyệt" page | The teacher is already on the document; a filter is one click, a page is navigation |
| Points per question in the bank | A question is worth different points in different papers (A-04 keeps the exam as the owner) |
| An "undo" stack for review decisions | A re-decision is the same command as a decision; a stack is state to keep and to explain |

## Domain model
No schema change. `review_state` is derived: `pending` when needs_review + flagged + spot_pending > 0, `done` when
nothing is undecided, `in_progress` otherwise.

## Contracts
| Method & path | Notes |
| --- | --- |
| `POST /review/documents/search` | rows gain `review_state`, `pending`; both filterable, `review_state` sortable |
| `POST /review/documents/{id}/questions/search` | `state` (pending default / approved / rejected / duplicate / all) + the search contract |
| `PATCH /questions/{id}`, `POST /questions/bulk` | unchanged; used to re-decide |

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Chosen filter on the document | URL (`useTableQuery`) | navigation |
| Review decisions | `questions.status` | until changed |

## Error taxonomy
| Condition | Code | HTTP |
| --- | --- | --- |
| Unknown `state` value | `bad_filter` | 422 |
| Re-deciding a question of another org | `not_found` | 404 |

## Observability
A re-decision is an ordinary status change and is audited like the first one.

## ADRs

### ADR-01 — One derived state per document, the counts behind it
**Context:** Six badges in a column answer a question nobody asked; the one people ask ("is there work left?")
cannot be filtered.
**Decision:** Derive `review_state` from the counts, make it the visible column and the filter, and keep the
breakdown one click away.
**Consequences:** The list is scannable and filterable; the detail is still there for whoever wants it.
**Status:** accepted

### ADR-02 — A decision is a state, not an event
**Context:** Approving is a keystroke and today it is final from the review page.
**Decision:** The document page can show any state and re-decide through the same command that decided first; no
undo stack, no new endpoint.
**Consequences:** A mistake costs one correction, not a database edit; nothing new to keep consistent.
**Status:** accepted

### ADR-03 — The 5% sample keeps its purpose and gets a name
**Context:** "Kiểm tra ngẫu nhiên" reads as a defect, not as a quality check on the automation.
**Decision:** Rename to "Mẫu kiểm chứng" and say in one sentence what it is: 5% of the questions the machine
approved by itself, drawn to catch it being wrong.
**Consequences:** The count stops being alarming; the check keeps working.
**Status:** accepted
