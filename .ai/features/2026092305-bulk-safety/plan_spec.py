# python3 scripts/gen_plan.py .ai/features/2026092305-bulk-safety .ai/features/2026092305-bulk-safety/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="history", title="A history worth restoring: a wider snapshot and a batch id",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Đổi mức độ cho 3 câu → review_events có 3 dòng cùng một batch_id",
               "Mỗi dòng ghi đủ môn, lớp, mức độ, chuyên đề và tag trước/sau",
               "POST /question-events/search trả một dòng cho cả lượt sửa, kèm lý do nếu không hoàn tác được"],
         in_scope=["snapshot widening", "batch_id migration", "events search"]),
    dict(id="UOW-02", slug="undo", title="Hoàn tác: a bulk edit restored as one unit",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["POST /questions/bulk/undo với batch vừa sửa → các câu trở lại đúng như cũ",
               "Một câu đã bị xóa → từ chối cả lượt, nêu tên câu",
               "Hoàn tác lần hai → 409, lượt hoàn tác cũng nằm trong lịch sử"],
         in_scope=["undo command", "guards on restore", "undo recorded as an event"]),
    dict(id="UOW-03", slug="bank-safety", title="The bank: undo in the toast, recent changes, and a count on every action",
         requirements=["US-01", "US-02", "US-03"], risk="low",
         demo=["Đặt Lớp 12 nhầm cho 2 câu → toast có Hoàn tác → hai câu trở lại như cũ",
               "Thay đổi gần đây: ai, lúc nào, sửa gì, mấy câu — hoàn tác từng lượt",
               "Mỗi nút bulk nói rõ sẽ đổi bao nhiêu câu"],
         in_scope=["toast undo", "recent changes sheet", "counts on the bulk actions"]),
    dict(id="UOW-04", slug="back-links", title="A way back from every detail page",
         requirements=["US-04"], risk="low",
         demo=["Báo cáo bài giao, kết quả bài làm, thêm câu hỏi, xem trước câu hỏi: đều có đường về danh sách"],
         in_scope=["BackLink on the four pages that lack one"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Widen what a review event records", layer="domain", estimate="3h",
  verifies=["AC-01"], assumptions=["A-02"],
  tests=[f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/domain/entities.py", f"{M}/bank/application/common.py",
           f"{M}/bank/application/commands/bulk_update_questions.py"],
  context="ADR-01. The snapshot must carry every field the bulk bar can change, topics and tags included.",
  done_when=["snapshot() covers status, difficulty, grade, subject, topics with primary, tags",
             "set_topics and set_tags record a before, not only an after",
             "Existing events still read back without raising"])
t(id="T-01-02", uow="UOW-01", title="batch_id on review_events", layer="data", estimate="2h",
  verifies=["AC-03"], assumptions=["A-01"],
  tests=[f"{API}/tests/test_bank_api.py"],
  touches=[f"{API}/alembic/versions", f"{API}/app/shared/infrastructure/schema/bank.py",
           f"{M}/bank/infrastructure/repositories.py", f"{M}/bank/domain/ports.py"],
  context="ADR-01. Nullable column plus two indexes; no backfill.",
  done_when=["Migration up and down", "alembic check clean", "One request writes one batch id"])
t(id="T-01-03", uow="UOW-01", title="POST /question-events/search — one row per batch", layer="api", estimate="4h",
  depends_on=["T-01-01", "T-01-02"], verifies=["AC-03", "AC-05"], assumptions=["A-05", "A-06"],
  tests=[f"{API}/tests/test_bank_api.py", f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py", f"{M}/bank/application/queries",
           f"{M}/bank/interface/router.py", f"{M}/bank/interface/schemas.py"],
  context="ADR-02. Search contract: {page, limit, filters} → {data, total, page, limit}.",
  done_when=["One row per batch with actor, fields, question count",
             "undoable plus a reason when false", "Org-scoped"])
t(id="T-02-01", uow="UOW-02", title="UndoBatch: restore a batch through the aggregate", layer="api", estimate="4h",
  depends_on=["T-01-01", "T-01-02"], verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-03"],
  tests=[f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/application/commands/undo_batch.py", f"{M}/bank/domain/services/history.py"],
  context="ADR-04. Same guards as an edit; all or nothing.",
  done_when=["Every field of the before restored", "A missing question refuses the whole batch",
             "subject_topic_conflict still applies"])
t(id="T-02-02", uow="UOW-02", title="The undo is itself an event, and cannot run twice", layer="api", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-04", "AC-05"], assumptions=["A-04", "A-06"],
  tests=[f"{API}/tests/test_bank_api.py"],
  touches=[f"{M}/bank/application/commands/undo_batch.py", f"{M}/bank/interface/router.py",
           f"{M}/bank/interface/schemas.py"],
  context="ADR-02, ADR-04.",
  done_when=["undo events under a new batch naming the one undone", "409 on a second undo",
             "422 past the window, naming its age"])
t(id="T-03-01", uow="UOW-03", title="Hoàn tác in the toast", layer="web", estimate="3h",
  depends_on=["T-02-02"], verifies=["AC-01"], assumptions=["A-01"],
  tests=[f"{S}/__tests__/bank-bulk.test.tsx"],
  touches=[f"{S}/hooks/page-hooks/bank/use-bulk-actions.ts", f"{S}/hooks/react-query/use-query-question.ts",
           f"{S}/services/question.service.ts"],
  context="The mutation answers with the batch id; the toast's action undoes it and refetches.",
  done_when=["Toast carries Hoàn tác", "Restored count reported", "List and facets refresh"])
t(id="T-03-02", uow="UOW-03", title="Thay đổi gần đây", layer="web", estimate="4h",
  depends_on=["T-01-03", "T-02-02"], verifies=["AC-03", "AC-04", "AC-05"], assumptions=["A-05", "A-06"],
  tests=[f"{S}/__tests__/bank-history.test.tsx"],
  touches=[f"{S}/components/page-components/Bank/RecentChanges/RecentChanges.tsx",
           f"{S}/hooks/page-hooks/bank/use-recent-changes.ts", f"{S}/components/page-components/Bank/BankPage.tsx"],
  context="ADR-02. One row per batch, newest first; a row that cannot be undone says why.",
  done_when=["Rows show when, who, fields, count", "Undo from a row", "A stale row states its reason"])
t(id="T-03-03", uow="UOW-03", title="Each bulk action names what it will change", layer="web", estimate="2h",
  verifies=["AC-06"],
  tests=[f"{S}/__tests__/bank-bulk.test.tsx"],
  touches=[f"{S}/components/page-components/Bank/BulkBar/BulkBar.tsx"],
  context="The selection count sits at the far right today, away from the buttons that act on it.",
  done_when=["Count on the actions", "Disabled with nothing selected", "Toolbar keeps its shape"])
t(id="T-04-01", uow="UOW-04", title="Back links on the four detail pages", layer="web", estimate="2h",
  verifies=["AC-07"], assumptions=["A-08"],
  tests=[f"{S}/__tests__/assignment-report.test.tsx"],
  touches=[f"{S}/components/page-components/AssignmentReport/AssignmentReportPage.tsx",
           f"{S}/components/page-components/AttemptResult/AttemptResultPage.tsx",
           f"{S}/components/page-components/QuestionNew/QuestionNewPage.tsx",
           f"{S}/components/page-components/QuestionPreview/QuestionPreviewPage.tsx"],
  context="Same component, same place as the detail pages that already have one.",
  done_when=["BackLink on all four", "Each points at the list it belongs to"])
TICKETS = T
