# Demo evidence — ui-polish-dialogs-tables

## UOW-01 — Dialogs, tables, spacing (2026-09-22)
- Every FormDialog: ⤢ "Phóng to" / ⤡ "Thu nhỏ" (tooltip), double-click on the title toggles, 8 resize handles
  (edges + corners, hidden on phones), clamped to the window, reset on close (`form-dialog.test.tsx`).
- Live (in-app browser, pane hidden): "Tải đề lên" dialog 730 px → Phóng to fills the window. The drag itself could
  not be measured live because the hidden pane does not run the open animation; covered by the jsdom test
  (right edge +200 px → width +400 px, height clamped to 180 px). To check by eye at the final review.
- DataTable: bordered columns (header, filter row, cells) and zebra rows (`even:bg-muted/40`), measured live on
  Đề đã tải lên (1 px column borders, tinted even rows); sticky header and filter row unchanged.
- Spacing: main padding 8 px on phones, 12 px ≥ sm, 16 px ≥ lg (was 16/24); PageHeader margin 8–12 px.

## UOW-02 — Back and question editor (2026-09-22)
- Live: /org/documents?page=2 → open a document → "← Đề đã tải lên" → back on page 2 ("Hiển thị 21–40 trên 51").
  Found while testing: during Next's page swap the old list renders once with the new URL's empty search; the list
  URL is now read from the address bar (`list-memory.test.tsx`).
- Used by Ngân hàng câu hỏi, Đề đã tải lên, Đề thi, Lớp học, Duyệt câu hỏi detail pages and "Hủy" on new question.
- TopicPicker is a tree everywhere it is used (question editor, bulk actions, review queue, exam matrix): collapsed
  branches, search keeps ancestors, ↑/↓/→/Enter/Esc.
- ⌘/Ctrl + Enter saves from anywhere on the page, also while a Vietnamese IME composes (`key` = "Process",
  `code` = "Enter"); button hint "⌘ Enter" on Apple devices (`question-edit.test.tsx`).
- 134 web tests, tsc, eslint, next build clean.
