---
feature: review-ux
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | A document has one readable state derived from its counts: `cần xem` (anything pending), `đang duyệt` (some approved, none pending), `xong` (every question decided) — a filterable, sortable column, with the detailed counts kept behind it | high | yes | Review list | confirmed | Confirmed by Loc Tran in chat (2026-09-23): "nhiều label, không filter, quá rối" |
| A-02 | The 5% sample stays and is renamed "Mẫu kiểm chứng", with one sentence on screen saying what it is for | high | no | Review list | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-03 | The review page lists every question of the document with a state filter (mặc định "Cần xem"), and any question can be opened, edited and re-decided — including undoing an approval | high | yes | Review page | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-04 | Points stay where they are (per type on the exam, per question override, scaled to 10); this feature only makes them visible and explains the total | high | no | Exam screen | confirmed | Confirmed by Loc Tran in chat (2026-09-23): "điểm đã đủ, chỉ khó tìm" |
| A-05 | Re-deciding a question is the existing bulk/status command; no new endpoint and no audit change beyond what a status change already records | medium | no | API | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — to confirm at final review |
