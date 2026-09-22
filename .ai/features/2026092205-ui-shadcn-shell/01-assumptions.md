---
feature: ui-shadcn-shell
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | shadcn style new-york, base colour neutral, brand blue as `--primary`; font Be Vietnam Pro kept | high | no | Look & feel | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | Theme default follows the OS; the choice (light/dark/system) is stored per browser by next-themes | high | no | Theme | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Table toolbar actions per screen: Thêm mới, Sửa (1 selected), Xóa (≥1, confirm), Nạp; Nhập/Xuất only where import/export exists (users) | medium | no | Toolbar | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Column filters: text = case/accent-insensitive contains (unaccent ILIKE), select = exact, date = from/to; debounce 300 ms; page sizes 20/50/100, default 20 | high | no | Filtering | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | URL param names: `q`, `page`, `page_size`, `sort` (`field` or `-field`), and one param per column filter named after the API field | high | yes | Links, API | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Bare-list endpoints become `Page`; small reference lists used by pickers (topics tree, taxonomy, tags for pickers) keep an unpaged variant via `page_size=all` capped at 1000 | medium | no | API | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Students use the same shell; header org switcher shows the current org only until F7 | high | no | Shell | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Detail panel under the table (back-office "Chi tiết") for exams → questions and classes → students; other lists open a page or dialog | medium | no | Layout | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Existing web tests are rewritten against the new markup; coverage kept at least at today's 84 cases | high | no | Tests | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
