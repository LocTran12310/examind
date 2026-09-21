---
feature: exam-practice
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | An exam is an ordered list of questions grouped in sections by type (Phần I MCQ, II true/false, III short answer, IV essay); points per question default by type and can be overridden per exam | high | yes | Exam model, grading | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | True/false partial credit (THPT 2025): 1 correct statement 0.1, 2 → 0.25, 3 → 0.5, 4 → 1 × question points; 0 correct → 0 | high | yes | Scores | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Short answers compare after normalisation: trim, comma = dot decimal, fractions a/b evaluated, numeric equality within 1e-9; otherwise case-insensitive text equality without accents | medium | no | Grading of short answers | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Blueprint rows: {topic_id (subtree) or tag_id, type, difficulty?, count}; questions drawn from usable questions at random with a seed; the same question never appears twice; rows that cannot be filled report the shortfall | medium | yes | Builder | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | Assignment: exam → one or more classes and/or students, open_at, close_at, duration (minutes), max_attempts (default 1), shuffle questions/options, results policy (after_submit / after_close / never) | medium | yes | Taking flow | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Attempt deadline = min(started_at + duration, close_at) + 30 s grace; after it the attempt is finalised with the saved answers | high | yes | Integrity | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Answers autosave on every change (debounced 500 ms client-side); the server stores the latest value per question | high | no | Data loss | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Essays are graded by teachers (score 0..points + comment); an attempt with ungraded essays shows "Đang chấm" for those points | medium | no | Results | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Stats are computed from `answer_facts` (one row per graded answer with the question's primary topic path, tag ids, type, difficulty, points, max) and roll up topic levels with ltree | medium | yes | Reports | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-10 | Students see only their own attempts and assignments of their classes; teachers see everything in the org | high | no | Permissions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-11 | Questions used by an exam cannot be hard-deleted (bank delete → 409); editing a question after an exam was taken does not change past answers' grades (answers store the graded snapshot) | high | no | History integrity | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-12 | Tab switches during an attempt are counted and shown to the teacher; no blocking | medium | no | Integrity | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
