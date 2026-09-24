---
feature: history-keeps-ids
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | The fix is to drop the foreign key on `review_events.question_id`, not to add a second column beside it | high | yes | Bank history | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-24). Two columns holding the same id would disagree the first time one of them was written alone; an audit log referring to a mutable table is where a foreign key does harm rather than good |
| A-02 | Rows already nulled cannot be recovered and are left as they are | high | no | History | confirmed | Accepted under blanket pre-approval; the id is simply not in the database any more |
| A-03 | An undo blocked by a deleted question still refuses the whole batch, and now names the ids | high | no | Bank | confirmed | Accepted under blanket pre-approval; naming is what was missing, not the refusal |
| A-04 | The downgrade re-creates the foreign key and, to be able to, nulls the ids of questions that no longer exist — so it is not loss-free, and says so | medium | no | Migrations | confirmed | Accepted under blanket pre-approval; a downgrade that silently fails on a real database is worse than one that states its cost |
