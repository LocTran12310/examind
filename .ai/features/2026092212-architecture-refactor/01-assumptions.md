---
feature: architecture-refactor
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | The API contract may change (web is the only client): list endpoints become `POST /<resource>/search` with typed filter objects and return `{data,total,page,limit}`; errors become `{code,message,details}` | high | yes | Every list and form | confirmed | Confirmed by Loc Tran in chat (2026-09-22): "Cho phép đổi" |
| A-02 | JSON stays snake_case and auth stays in httpOnly cookies | high | no | All payloads | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-03 | Next.js App Router stays; the folder convention is applied inside `src/` | high | yes | Web | confirmed | Confirmed by Loc Tran in chat (2026-09-22) |
| A-04 | Every API module gets the four layers, simple CRUD included | high | yes | API | confirmed | Confirmed by Loc Tran in chat (2026-09-22) |
| A-05 | Domain objects are plain dataclasses mapped imperatively by SQLAlchemy; the schema and Alembic history do not change | medium | no | Persistence | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-06 | Table state stays in the URL; the web converts it to the search body | high | no | Lists, back navigation | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-07 | Ingestion algorithms (MathType, splitter, header, vector images) move without behaviour change; the official golden numbers must not move | high | no | Ingestion | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
| A-08 | Existing HTTP tests are updated for the new URLs/shapes only; their assertions keep their meaning | high | no | Test trust | confirmed | Accepted under blanket pre-approval by Loc Tran (chat, 2026-09-22) — to confirm at final review |
