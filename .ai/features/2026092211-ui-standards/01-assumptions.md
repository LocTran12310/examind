---
feature: ui-standards
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Same content (SHA-256) is never stored twice; the choice is skip (default) or re-parse the existing document. Same name + different content: replace the newest same-name document (default), keep both, or skip | high | yes | Upload data | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "không có options ghi đè hay bỏ qua" — defaults accepted under blanket pre-approval |
| A-02 | Operators and labels (text * = + - !, compare = < ≤ > ≥); Examind keeps them in the URL as `<col>_op` instead of a POST body, because list state lives in the URL | high | no | Filters | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Text equality is accent/case-insensitive (not an exact match); dates default to a range (existing links) with = < ≤ > ≥ for one day | medium | no | Filters | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Business zone Asia/Ho_Chi_Minh (setting BUSINESS_TZ): display, day filters, school-year/term of an answer, default school year; timestamps stay UTC timestamptz, API ISO `Z`; datetime inputs send +07:00 | high | yes | Reports, filters | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) |
| A-05 | Reordering stays within a PHẦN (the server orders by section) | high | no | Exam builder | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
