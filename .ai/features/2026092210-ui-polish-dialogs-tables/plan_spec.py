# Source spec — python3 scripts/gen_plan.py .ai/features/2026092210-ui-polish-dialogs-tables .ai/features/2026092210-ui-polish-dialogs-tables/plan_spec.py
WEB = "apps/web"

UOWS = [
    dict(dod_done=True, id="UOW-01", slug="dialogs-tables-spacing", title="Resizable dialogs, bordered zebra tables, compact spacing",
         requirements=["US-01", "US-02", "US-05"], risk="low",
         demo=["Tags → Thêm tag → ⤢ Phóng to → Thu nhỏ → drag the right edge", "Người dùng list: column borders, zebra rows",
               "Phone width: page padding 8 px"],
         in_scope=["FormDialog", "DataTable styles", "AppShell/PageHeader spacing"]),
    dict(dod_done=True, id="UOW-02", slug="back-and-editor", title="Back keeps list state; topic tree and ⌘+Enter in the question editor",
         requirements=["US-03", "US-04"], risk="low",
         demo=["Bank page 2 + filter → open a question → ← returns to page 2", "Sửa câu → Chọn chuyên đề shows the tree → pick → ⌘ Enter saves"],
         in_scope=["list-memory + BackLink", "TopicTreePick", "useSaveShortcut"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="FormDialog maximise + edge/corner resize", layer="web", estimate="3h", verifies=["AC-01"],
  tests=[f"{WEB}/src/__tests__/form-dialog.test.tsx"], touches=[f"{WEB}/src/components/app/FormDialog.tsx"], assumptions=["A-01"],
  context="ADR-01.", done_when=["Maximise", "Resize edges", "Clamp"])
t(id="T-01-02", uow="UOW-01", title="DataTable borders + zebra; compact spacing", layer="web", estimate="2h", verifies=["AC-02", "AC-06"],
  tests=[f"{WEB}/src/__tests__/data-table.test.tsx"], touches=[f"{WEB}/src/components/data-table/DataTable.tsx", f"{WEB}/src/app/(app)/AppShell.tsx", f"{WEB}/src/components/app/PageHeader.tsx"],
  context="", done_when=["Borders", "Zebra", "Spacing"])
t(id="T-02-01", uow="UOW-02", title="List memory + BackLink on detail pages", layer="web", estimate="2h", verifies=["AC-03"],
  tests=[f"{WEB}/src/__tests__/list-memory.test.tsx"], touches=[f"{WEB}/src/lib/list-memory.ts", f"{WEB}/src/components/app/BackLink.tsx", f"{WEB}/src/components/data-table/useTableQuery.ts",
  f"{WEB}/src/app/(app)/org/bank/[id]/page.tsx", f"{WEB}/src/app/(app)/org/bank/new/page.tsx", f"{WEB}/src/app/(app)/org/exams/[id]/page.tsx", f"{WEB}/src/components/documents/DocumentDetail.tsx"],
  assumptions=["A-02"], context="ADR-02.", done_when=["Stored per list", "Back links use it"])
t(id="T-02-02", uow="UOW-02", title="Topic tree picker + ⌘/Ctrl+Enter in question editors", layer="web", estimate="3h", verifies=["AC-04", "AC-05"],
  tests=[f"{WEB}/src/__tests__/question-edit.test.tsx", f"{WEB}/src/__tests__/bank-bulk.test.tsx", f"{WEB}/src/__tests__/exam-builder.test.tsx"], touches=[f"{WEB}/src/components/topics/TopicTreePick.tsx", f"{WEB}/src/lib/shortcuts.ts", f"{WEB}/src/components/bank/QuestionForm.tsx", f"{WEB}/src/components/review/QuestionEditor.tsx"],
  assumptions=["A-03", "A-04"], context="", done_when=["Tree", "Cmd+Enter", "Hint"])

TICKETS = T
