---
feature: adaptive-review
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Mastery per (student, leaf topic) = exponential moving average of answer correctness with α = 0.3, where each answer's weight grows with difficulty (nb 0.8, th 1.0, vd 1.2, vdc 1.4); starts at 0.5 with the first answer | medium | yes | Mastery values, review selection | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | Parents' mastery = answered-weighted average of descendants (computed at read time) | high | no | Display | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Review exam default 20 questions: 60% from the 3 weakest leaf topics (mastery < 0.8, ≥ 1 answer), 30% from medium topics (0.5–0.8), 10% re-ask of questions answered wrong ≥ 24 h ago; fill from weakest topics' neighbours when short | medium | yes | Generator | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Target difficulty by mastery: < 0.4 → nb/th, 0.4–0.7 → th/vd, > 0.7 → vd/vdc; questions without difficulty count as th | medium | no | Generator | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | Questions answered correctly in the last 7 days are excluded from new review exams; flagged/non-usable questions are always excluded | high | no | Generator | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Student self-practice: untimed-in-practice but capped at 60 minutes, results shown immediately, no attempt limit; stored as attempts without assignment | medium | no | Practice flow | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Teacher "đề ôn cá nhân" for a class creates one adaptive exam per student and one assignment per student (window + duration from the dialog) | medium | yes | Assignment model | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Suspect key rule: a MCQ with ≥ 10 graded answers where the top-quartile students (by attempt score) chose one other option at least 60% of the time → status `flagged` with issue "Nghi sai đáp án" and the evidence stored; also flagged when overall correctness < 15% with ≥ 20 answers | medium | no | Flag precision | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Detection runs in the worker every 10 minutes and on demand; flagged questions reappear in the review queue of their source document (or a "Câu bị gắn cờ" list for manual questions) | medium | no | Review workflow | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
