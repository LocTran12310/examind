---
feature: pickers-builder
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | A topic picker opened for a question starts on that question's best suggestion (expanded and focused, not applied); with no suggestion it opens as today | high | yes | Tagging, review | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-02 | The number beside a topic is the count of **questions** in that subtree, scoped to the subject and to usable questions; the count of child topics is not shown | high | yes | Every picker | confirmed | Confirmed by Loc Tran in chat (2026-09-23): "hiển thị thêm số câu hỏi hiện có của mỗi chuyên đề" |
| A-03 | "Gán theo gợi ý" applies each selected question's own top suggestion in one request; questions without a suggestion are left untouched and reported | high | yes | Tagging queue | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-04 | The bank's bulk actions gain subject and grade, with the same staff permission as the other bulk edits | high | no | Bank | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-05 | A blueprint row on a topic with no usable question is refused with a message naming the topic, not silently returning fewer questions | medium | no | Exam builder | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) — to confirm at final review |
| A-06 | "Đổi câu" offers both paths: the automatic replacement it does today, and choosing from the bank with the filters already used by the builder | high | no | Exam builder | confirmed | Confirmed by Loc Tran in chat (2026-09-23) |
| A-07 | Long option lists (documents, classes) scroll inside the dropdown and load further pages as they scroll | medium | no | Filters | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-23) |
