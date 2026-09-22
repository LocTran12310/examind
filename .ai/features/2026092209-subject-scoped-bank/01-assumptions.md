---
feature: subject-scoped-bank
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Subject is the working context of the bank: tabs at the top, always one chosen; questions without a subject have their own "Chưa phân môn" tab (shown only when there are any) | high | yes | Bank layout | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Bộ lọc nên phân theo từng môn" — tab form accepted under blanket pre-approval, to confirm at final review |
| A-02 | Tags get an optional subject; no subject = shared by all subjects; source tags (nguồn đề) are always shared; backfill gives a tag the subject of its questions when they all share one | medium | yes | Tag data | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | The chosen subject is remembered per browser and org (localStorage), like the header year selector — not in the user row as the plan first said | medium | no | Convenience | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Filters live in a right-side "Bộ lọc" sheet with sections and counts; counts are computed with every other filter applied (a facet ignores its own dimension); topic counts include the subtree | high | no | Filter UX | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "nên để bộ lọc filter dropdown dialog hay đại loại thế" — sheet form accepted under blanket pre-approval |
| A-05 | The sheet edits a draft and applies on "Áp dụng"; chips remove one filter at once; the search box stays on the page | medium | no | Filter UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | "Năm học" filters by the source document's school year (manual questions have none) | medium | no | Filter | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | The exam matrix (BlueprintEditor) lists topics and tags of the exam's subject only | high | no | Exam builder | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
