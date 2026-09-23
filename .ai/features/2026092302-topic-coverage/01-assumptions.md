---
feature: topic-coverage
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Suggestions are computed on demand (no stored suggestion rows): keyword cues first, then kNN over already-tagged questions of the same subject, returning the three best candidates with their score and where they came from | high | yes | Tagging queue | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
| A-02 | A question the pipeline could not classify is stored `needs_review` instead of `auto_approved`, whatever its parsing confidence; the review reason says "chưa gắn chuyên đề" | high | yes | Ingestion, review queue | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — it is what let 101 questions go silent |
| A-03 | The tagging queue is a screen of its own under Duyệt câu hỏi, not a new mode inside the review queue: the work is one decision per question and benefits from bulk apply | medium | no | Web layout | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — to confirm at final review |
| A-04 | The existing 101 auto-approved untagged questions keep their status; tagging them does not push them back to review | high | no | Existing bank | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
| A-05 | ~~The tagging model (LLM) is not called from the queue~~ — **superseded 2026-09-23 by measurement**: keyword + kNN covered 14 of 102 questions (13 kNN, 2 keyword), because the backlog is exactly what the cues already failed on. The model is now called for questions the rules cannot place | medium | no | Suggestion quality | resolved | Measured on the live backlog during UOW-01; G3 reopened and UOW-03 added (Loc Tran, chat 2026-09-23) |
| A-06 | The model suggests, never decides: its candidates are shown with source `ai`, a teacher still confirms, and a model failure or timeout degrades to the rule-based candidates instead of failing the request | high | yes | Suggestion quality, latency | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
| A-07 | Model suggestions are asked for one visible page at a time (batches of ~10 questions per call, as ingestion does), only for questions with no candidate or a weak best candidate | high | no | Latency, cost | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
