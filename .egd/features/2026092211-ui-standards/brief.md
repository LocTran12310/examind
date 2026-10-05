# Duplicate uploads, Filter operators, business time zone, shadcn everywhere

## Problem
Loc Tran (chat, 2026-09-22): uploading files already uploaded created duplicates with no "ghi đè / bỏ qua"
choice (critical); tables need back-office operators (>, <, =, …) with one FE/BE mapping;
timestamps must match between UTC server and client consistently; raw HTML tags remain where shadcn has
components; reordering exam questions saves on every click and the list jumps; the maximised exam
preview dialog shows a white band at the bottom.

## Outcome
---
feature: ui-standards
slug: 2026092211-ui-standards
owner: Loc Tran
created: 2026-09-22
status: approved
---

## Success signal
Uploading the 18 reference files again reports 18 "đã có" and stores nothing; a document created 00:30 in Hà Nội
is found under that day; the exam preview fills the maximised dialog.

## Out of scope
- Server-side deduplication by content similarity (different files with the same questions)

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Uploader | Same exam uploaded twice → two documents | Told per file: same content → skip or re-parse; same name → replace, keep both or skip |
| Anyone filtering | Contains / ranges only | Operator per column: text * = + - !, numbers and dates = < ≤ > ≥, date range |
| Anyone reading times | Browser zone, date filters in UTC days | Asia/Ho_Chi_Minh display and day filters, whatever the browser/server zone |
| Exam author | ↑/↓ saves each move, list jumps | Draft order: swap with a chosen position, drag, ↑/↓, save once |

## Constraints
| Kind | Detail |
| --- | --- |
| Filters | URL search params stay the state; server-side filtering |
| UI | components/ui untouched (CLI files) |
