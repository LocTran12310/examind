---
feature: bulk-safety
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | One bulk action is one undoable unit: every question it touched is restored together, or none is | high | yes | Bank, history | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — the complaint is "khó tìm lại được", and a half-undone batch is worse than none |
| A-02 | The snapshot a review event records widens to cover everything the bulk bar can change: status, difficulty, grade, subject, primary topic, the whole topic list and tags | high | yes | Bank, review history | confirmed | Accepted under blanket pre-approval. Without it there is nothing to restore — this is the defect, not a feature |
| A-03 | Undo restores the recorded `before` **as it was**, even if the question changed again afterwards, and says so; it does not attempt a three-way merge | medium | no | Bank | confirmed | Accepted under blanket pre-approval. A merge nobody asked for is a second surprise on top of the first |
| A-04 | An undo is itself a recorded event (`undo`), so the history never loses a step and an undo cannot be undone twice | high | no | History | confirmed | Accepted under blanket pre-approval; `review_events` is append-only by design |
| A-05 | "Thay đổi gần đây" lists the batches of the organisation, newest first, with who, when, what changed and how many questions — not one row per question | medium | no | Bank | confirmed | Accepted under blanket pre-approval; a 20-question batch as 20 rows is the same wall of labels Loc Tran already objected to |
| A-06 | A batch older than a fixed window can still be read but no longer offers undo, so an "undo" never quietly reverses a month of work | medium | no | Bank | confirmed | Accepted under blanket pre-approval; the window is 7 days (ADR-02) |
| A-07 | Questions in the bank do **not** get a default point value; points stay a property of the paper (`points_by_type` plus the per-question override) | high | no | Exams, bank | confirmed | Recommended by me and open for Loc Tran at final review — see ADR-03 |
| A-08 | Every detail page carries a back link to its list: assignment report, attempt result, new question, question preview | high | no | Web | confirmed | Confirmed by Loc Tran in chat (2026-09-23): "không có nút back về trang trước đó?" |
