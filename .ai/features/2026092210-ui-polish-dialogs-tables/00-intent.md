---
feature: ui-polish-dialogs-tables
slug: 2026092210-ui-polish-dialogs-tables
owner: Loc Tran
created: 2026-09-22
status: approved
---

# Intent — Dialogs, tables, navigation and small screens for dense screens

## Problem
Loc Tran (chat, 2026-09-22, with reference screenshots):
- dialogs cannot be maximised or resized from their edges;
- tables need visible column borders and alternating row backgrounds (sticky header and filter row stay);
- going to a detail page from page 2 and pressing "←" returns to page 1;
- "Chuyên đề" in the question editor is a flat list, not the tree; the button says Ctrl+Enter but Cmd+Enter
  does nothing on a Mac;
- spacing between the tables and the side/header panels wastes room on small screens (mobile later).

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Teacher / admin | Fixed-size dialogs | ⤢ Phóng to / Thu nhỏ, drag any edge or corner |
| Everyone on lists | Plain rows | Bordered columns, zebra rows, sticky header + filters |
| Reviewer | Loses page and filters after a detail page | Returns to the same page, sort and filters |
| Question editor | Flat topic list, Ctrl-only hint | Topic tree with search; ⌘/Ctrl + Enter saves |
| Phone / small laptop | Wide paddings | Compact paddings, more rows visible |

## Success signal
From page 2 of Ngân hàng câu hỏi with a filter, open a question, press "← Ngân hàng câu hỏi": the same page and
filter are shown. Any form dialog can be maximised and resized by dragging its edges.

## Out of scope
- Remembering dialog sizes between visits
- A dedicated mobile layout

## Constraints
| Kind | Detail |
| --- | --- |
| UI | shadcn primitives unchanged (`components/ui/` is CLI-only); behaviour lives in `components/app/*` |
