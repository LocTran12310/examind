---
feature: question-review
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Statuses: `draft` (legacy) → at ingestion `auto_approved` or `needs_review`; teacher actions give `approved` / `rejected`; `duplicate` for near-duplicates. `auto_approved` and `approved` are both usable in exams | high | yes | Every later query on "usable" questions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-02 | Auto-approve needs confidence ≥ org threshold (default 0.85) AND an answer (except essays) AND no blocking issue (`thiếu phương án`, `thiếu đáp án`, `đáp án không khớp…`, `OCR`, `AI không phản hồi`, `không nhận ra phương án`) | medium | yes | Review volume | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Near-duplicate = same org, same type, trigram similarity of normalised stem+options ≥ 0.9 against a usable question; the new one becomes `duplicate` with `duplicate_of` | medium | no | Dedupe precision | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-04 | Source view: PDFs/scans show the rendered source page next to the question; Word files show no page image | medium | no | Review UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-05 | Keyboard map: Enter approve+next, 1–4 set MCQ answer A–D (a–d toggles for true/false), T topic search, E edit, X reject, J/K next/previous, S skip, ? help | high | no | Review UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Answer-key paste accepts "1A 2C 3B", "1.A, 2.C", "1-A", or a column of letters; applies to MCQ by number in the document (part-aware with "PHẦN I:" prefixes) | medium | no | Bulk answers | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Spot check: 5% (min 1) of auto-approved questions per document are queued as "Kiểm tra ngẫu nhiên"; if ≥ 2 of the last 20 spot checks in the org were rejected or edited, the org threshold rises by 0.05 (max 0.95) | medium | no | Threshold drift | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | kNN topic suggestion: when keyword score is weak (< 0.6) the primary topic of the most similar approved question (trigram ≥ 0.35) is suggested with source `knn` | medium | no | Suggestion quality | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-09 | Review assignment is per document (`assigned_to`), optional; queue filter "Của tôi" | medium | no | Team workflow | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-10 | Bank search: text (unaccented, trigram), subject, grade, semester, exam kind, topic subtree, tags (any), type, difficulty, status, source document; page size 20 | high | no | Bank UX | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-11 | Teachers edit any question of their org; students never see the bank | high | no | Permissions | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
