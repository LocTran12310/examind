---
feature: learning-telemetry
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Time on a question is measured client-side (the runner reports seconds per question when the answer is saved) and clamped server-side to the attempt window; it is evidence, not proof | high | yes | Timing data | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — to confirm at final review |
| A-02 | A question a student never opened or answered is excluded from mastery and from item statistics, whoever submitted the attempt (student or the expiry sweep) | high | yes | Mastery, item stats | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23): the current behaviour punishes abandoning practice |
| A-03 | "Weak topic" = mastery below 0.6 with at least 5 answers, one definition shared by the planner, the API and the UI; below the threshold with fewer answers it is "chưa đủ dữ liệu" | medium | yes | Practice plans, reports | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — thresholds to confirm at final review |
| A-04 | Mastery decays toward 0.5 with a half-life of 60 days of no answers on that topic, applied when the value is read or updated, never as a background job | medium | no | Mastery | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — to confirm at final review |
| A-05 | Item statistics are computed on demand from `answer_facts` (p-value, first-attempt correct, discrimination by top/bottom third of the attempt's score, distractor counts) and shown with the number of observations; below 10 observations they are marked "chưa đủ dữ liệu" | high | no | Question detail | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
| A-06 | A weekly mastery snapshot per (student, topic) is written by the worker on Mondays in business time and backfilled from facts, so trends exist before any screen shows them | high | no | Storage, trends | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
| A-07 | Recompute is an org-admin endpoint that replays the facts of one organisation inside one transaction; at the current volume (hundreds of thousands of facts) this is acceptable | medium | no | Operations | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — revisit if a centre exceeds ~10⁶ facts |
