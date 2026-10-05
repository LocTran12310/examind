---
feature: ui-polish-dialogs-tables
adr_count: 2
---

# Logical design — Dialogs, tables, navigation, small screens

## Approach
- `components/app/FormDialog.tsx`: state `maximized` and `size {w,h}`; the shadcn DialogContent gets inline
  width/height; `ResizeHandles` (right, left, bottom, top edges + corners) use pointer capture; a centred dialog
  grows by 2×Δ per edge so the edge stays under the pointer; clamped to the viewport. Header button ⤢/⤡ with tooltip.
- `DataTable`: `border-r` on cells except the last, `even:bg-muted/40` rows, compact paddings.
- `lib/list-memory.ts`: `useTableQuery` saves `pathname+search` per pathname in sessionStorage; `listHref(path)`
  returns it; `components/app/BackLink.tsx` renders the link. Used by bank, documents, exams, classes, review
  detail pages and the new-question page.
- `components/topics/TopicTreePick.tsx`: single-choice tree (search, expand, click to pick), used by QuestionForm
  instead of the flat TopicPicker.
- `lib/shortcuts.ts`: `useSaveShortcut(handler)` (window keydown, capture, `code === "Enter" || key === "Enter"`
  with meta/ctrl) and `saveHint()` ("⌘ Enter" / "Ctrl + Enter").
- Spacing: `main` `p-2 sm:p-3 lg:p-4`, PageHeader `mb-2 sm:mb-3`.

## Alternatives considered
| Option | Why not |
| --- | --- |
| CSS `resize: both` | Only the bottom-right corner, no left/top edges |
| Passing list state in the detail URL | Every link would need to carry it |

## Domain model
No change.

## Contracts
No API change.

## State ownership
| State | Owner | Lifetime |
| --- | --- | --- |
| Dialog size | component state | while open |
| Last list URL | sessionStorage per pathname | tab |

## Failure modes
| Condition | Code | HTTP | UI |
| --- | --- | --- | --- |
| No stored list URL | — | — | plain list link |

## Observability
None.

## ADRs

### ADR-01 — Resizing in the app wrapper, not the shadcn file
**Context:** `components/ui/` stays CLI-generated (F6).
**Decision:** FormDialog adds handles and inline size around shadcn DialogContent.
**Consequences:** Every FormDialog gains it at once.
**Status:** accepted

### ADR-02 — List memory in sessionStorage
**Context:** Back links lose the URL state.
**Decision:** The table query hook records the list URL; back links read it.
**Consequences:** Per tab, survives reloads, no URL changes.
**Status:** accepted
