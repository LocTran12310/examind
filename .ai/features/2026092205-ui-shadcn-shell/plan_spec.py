# Source spec for 04-units-of-work — regenerate with:
#   python3 scripts/gen_plan.py .ai/features/2026092205-ui-shadcn-shell .ai/features/2026092205-ui-shadcn-shell/plan_spec.py
API = "apps/api"
WEB = "apps/web"
UI = f"{WEB}/src/components/ui"

UOWS = [
    dict(id="UOW-01", slug="shell-theme", title="shadcn foundation, theme and app shell",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Sign in as trungtama/admin → left sidebar with icons, header right: org, theme, avatar menu",
               "Toggle Tối → whole app dark, refresh keeps it; collapse sidebar to icons",
               "Sign in as a student → same shell with student menu; phone width → menu opens as a sheet"],
         in_scope=["shadcn init + components", "ThemeProvider", "AppSidebar, header, OrgSwitcher (current org), UserMenu", "Login / change-password pages"]),
    dict(id="UOW-02", slug="data-table", title="Server-side DataTable with URL state on users, organisations, classes",
         requirements=["US-03", "US-04"], depends_on=["UOW-01"], risk="high",
         demo=["Users: type 'bui' in Họ tên filter → URL ?full_name=bui, request carries it, 20/page",
               "Open the copied URL in a new tab → same rows, inputs filled",
               "Tick 2 users → Xóa asks to confirm; Sửa disabled; Nạp reloads",
               "Organisations and Classes use the same table"],
         in_scope=["paging helper + endpoints", "DataTable, filter row, toolbar, pagination, useTableQuery", "Users, orgs, classes screens"]),
    dict(id="UOW-03", slug="lists", title="All remaining lists on the DataTable",
         requirements=["US-03", "US-04"], depends_on=["UOW-02"],
         demo=["Documents, review, exams, assignments, AI models, tags: column filters + paging from the server",
               "Exams: select a row → detail panel lists its questions",
               "Bank: filters on the left + search, pages from the server, cards unchanged"],
         in_scope=["Bare-list endpoints → Page", "List screens"]),
    dict(id="UOW-04", slug="flows", title="Every other screen on shadcn components, old barrel removed",
         requirements=["US-01", "US-04"], depends_on=["UOW-02"],
         demo=["Upload a document, review with hotkeys, edit a question, build and take an exam, see results and reports — in dark mode",
               "`grep -r \"@/components/ui\\\"\"` finds nothing; lint forbids it"],
         in_scope=["Forms/dialogs/editors/runner/reports/topic tree", "Delete components/ui/index.tsx", "ESLint rule"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="shadcn init (Tailwind v4 vars), theme tokens, components, next-themes",
  layer="web", estimate="3h", verifies=["AC-01", "AC-02"], tests=[f"{WEB}/src/__tests__/theme.test.tsx"],
  touches=[f"{WEB}/components.json", f"{WEB}/src/app/globals.css", f"{WEB}/src/app/layout.tsx", f"{WEB}/src/lib/utils.ts", f"{UI}/button.tsx", f"{WEB}/src/components/app/ThemeProvider.tsx", f"{WEB}/package.json"],
  assumptions=["A-01", "A-02"], context="ADR-01. Generate every component listed in the plan with the CLI.",
  done_when=["components.json committed", "Light and dark tokens", "Theme persists"])
t(id="T-01-02", uow="UOW-01", title="AppSidebar + header (OrgSwitcher, ThemeToggle, UserMenu), nav icons",
  layer="web", estimate="4h", depends_on=["T-01-01"], verifies=["AC-03", "AC-04", "AC-05"], tests=[f"{WEB}/src/__tests__/shell.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/AppShell.tsx", f"{WEB}/src/lib/nav.ts", f"{WEB}/src/components/app/AppSidebar.tsx", f"{WEB}/src/components/app/OrgSwitcher.tsx", f"{WEB}/src/components/app/UserMenu.tsx"],
  assumptions=["A-07"], context="One shell for all roles; sidebar collapsible to icons; sheet on mobile.",
  done_when=["Role-filtered menu", "Header right side as in the reference", "Mobile sheet"])
t(id="T-01-03", uow="UOW-01", title="Login and change-password on shadcn",
  layer="web", estimate="1h", depends_on=["T-01-01"], verifies=["AC-01"], tests=[f"{WEB}/src/__tests__/login.test.tsx"],
  touches=[f"{WEB}/src/app/(auth)/login/LoginForm.tsx", f"{WEB}/src/app/(auth)/change-password/page.tsx"],
  context="Card + Input + Label + Button.", done_when=["Login works", "Errors shown"])
t(id="T-02-01", uow="UOW-02", title="API paging helper (q, column filters, sort, page, page_size=all)",
  layer="api", estimate="3h", verifies=["AC-10"], tests=[f"{API}/tests/test_paging.py"],
  touches=[f"{API}/app/services/paging.py", f"{API}/migrations/versions/0011_list_search.py"], assumptions=["A-04", "A-05", "A-06"],
  context="ADR-03. unaccent ILIKE for text; bad sort → 422 bad_sort.", done_when=["Helper unit-tested", "unaccent contains", "bad_sort"])
t(id="T-02-02", uow="UOW-02", title="Users, orgs, classes endpoints on the paging helper",
  layer="api", estimate="3h", depends_on=["T-02-01"], verifies=["AC-10"], tests=[f"{API}/tests/test_paging.py", f"{API}/tests/test_users_api.py", f"{API}/tests/test_orgs_api.py", f"{API}/tests/test_classes_api.py", f"{API}/tests/test_import.py"],
  touches=[f"{API}/app/routers/users.py", f"{API}/app/routers/admin_orgs.py", f"{API}/app/routers/classes.py", f"{API}/app/services/users.py", f"{API}/app/services/orgs.py", f"{API}/app/services/classes.py"],
  context="Column filters named after fields.", done_when=["Page on all three", "Filters + sort", "< 300 ms on perf fixture"])
t(id="T-02-03", uow="UOW-02", title="DataTable: filter row, toolbar, selection, pagination, useTableQuery (URL)",
  layer="web", estimate="4h", depends_on=["T-01-01"], verifies=["AC-06", "AC-07", "AC-08", "AC-09"], tests=[f"{WEB}/src/__tests__/data-table.test.tsx"],
  touches=[f"{WEB}/src/components/data-table/DataTable.tsx", f"{WEB}/src/components/data-table/useTableQuery.ts", f"{WEB}/src/components/data-table/Pagination.tsx", f"{WEB}/src/components/data-table/Toolbar.tsx", f"{WEB}/src/components/data-table/FilterCell.tsx"],
  assumptions=["A-03", "A-04", "A-05"], context="ADR-02, ADR-04. Debounced text filters use router.replace.",
  done_when=["Debounce + URL", "Initial load from URL", "Confirm delete", "Footer text"])
t(id="T-02-04", uow="UOW-02", title="Users, organisations, classes screens on DataTable",
  layer="web", estimate="4h", depends_on=["T-02-02", "T-02-03", "T-01-02"], verifies=["AC-11"], tests=[f"{WEB}/src/__tests__/users.test.tsx", f"{WEB}/src/__tests__/orgs.test.tsx", f"{WEB}/src/__tests__/classes.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/users/page.tsx", f"{WEB}/src/app/(app)/admin/orgs/page.tsx", f"{WEB}/src/app/(app)/org/classes/page.tsx", f"{WEB}/src/components/org/UserForm.tsx", f"{WEB}/src/components/admin/OrgForm.tsx", f"{WEB}/src/components/org/MemberManager.tsx", f"{WEB}/src/components/org/ClassForms.tsx"],
  assumptions=["A-08"], context="Forms in Dialog; classes → students detail panel.", done_when=["Three screens", "Forms in dialogs", "Import/export kept on users"])
t(id="T-03-01", uow="UOW-03", title="Bare-list endpoints → Page (classes done; exams, assignments, tags, ai-models, review)",
  layer="api", estimate="3h", depends_on=["T-02-01"], verifies=["AC-10"], tests=[f"{API}/tests/test_paging.py", f"{API}/tests/test_exams_api.py", f"{API}/tests/test_review_flow.py"],
  touches=[f"{API}/app/routers/exams.py", f"{API}/app/routers/assignments.py", f"{API}/app/routers/tags.py", f"{API}/app/routers/ai_models.py", f"{API}/app/routers/review.py", f"{API}/app/routers/documents.py"],
  context="Old callers updated in the same change.", done_when=["All return Page", "Filters per column"])
t(id="T-03-02", uow="UOW-03", title="Documents, review, exams (+detail panel), assignments, AI models, tags screens",
  layer="web", estimate="4h", depends_on=["T-03-01", "T-02-03"], verifies=["AC-11"], tests=[f"{WEB}/src/__tests__/documents.test.tsx", f"{WEB}/src/__tests__/exams.test.tsx", f"{WEB}/src/__tests__/ai-models.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/documents/page.tsx", f"{WEB}/src/app/(app)/org/review/page.tsx", f"{WEB}/src/app/(app)/org/exams/page.tsx", f"{WEB}/src/app/(app)/org/ai-models/page.tsx", f"{WEB}/src/components/tags/TagManager.tsx"],
  assumptions=["A-08"], context="Detail panel for exams.", done_when=["All lists on DataTable", "Detail panel"])
t(id="T-03-03", uow="UOW-03", title="Question bank: shadcn filters, URL state, server paging",
  layer="web", estimate="3h", depends_on=["T-02-03"], verifies=["AC-11", "AC-08"], tests=[f"{WEB}/src/__tests__/bank.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/bank/page.tsx", f"{WEB}/src/components/bank/BankFilters.tsx", f"{WEB}/src/components/bank/BulkBar.tsx", f"{WEB}/src/components/bank/QuestionRow.tsx"],
  context="Cards kept; shared Pagination.", done_when=["Filters in URL", "Shared pagination"])
t(id="T-04-01", uow="UOW-04", title="Upload, document detail, review queue, question editor/form on shadcn",
  layer="web", estimate="4h", depends_on=["T-02-03"], verifies=["AC-12"], tests=[f"{WEB}/src/components/review/ReviewQueue.test.tsx", f"{WEB}/src/components/review/QuestionEditor.test.tsx", f"{WEB}/src/__tests__/upload.test.tsx"],
  touches=[f"{WEB}/src/components/documents/UploadForm.tsx", f"{WEB}/src/components/review/ReviewQueue.tsx", f"{WEB}/src/components/review/QuestionEditor.tsx", f"{WEB}/src/components/bank/QuestionForm.tsx"],
  context="Hotkeys unchanged.", done_when=["Hotkeys work", "Dialogs are shadcn"])
t(id="T-04-02", uow="UOW-04", title="Exam builder, assign, runner, results, essay grading, reports, adaptive, topic tree on shadcn",
  layer="web", estimate="4h", depends_on=["T-02-03"], verifies=["AC-12"], tests=[f"{WEB}/src/components/exams/ExamRunner.test.tsx", f"{WEB}/src/components/topics/TopicTree.test.tsx", f"{WEB}/src/__tests__/reports.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/exams/[id]/page.tsx", f"{WEB}/src/components/exams/ExamRunner.tsx", f"{WEB}/src/components/exams/ResultView.tsx", f"{WEB}/src/components/reports/Heatmap.tsx", f"{WEB}/src/components/topics/TopicTree.tsx"],
  context="Dark-mode colours via tokens; heatmap uses CSS vars.", done_when=["Runner works", "Heatmap readable in dark"])
t(id="T-04-03", uow="UOW-04", title="Remove old barrel, ESLint no-restricted-imports, full web test pass, build",
  layer="test", estimate="2h", depends_on=["T-04-01", "T-04-02", "T-03-02", "T-03-03", "T-02-04", "T-01-03"], verifies=["AC-01", "AC-12"],
  tests=[f"{WEB}/src"], touches=[f"{WEB}/src/components/ui/index.tsx", f"{WEB}/eslint.config.mjs"], assumptions=["A-09"],
  context="ADR-01.", done_when=["No import of the barrel", "Lint rule", "tsc/eslint/build clean", "Web tests ≥ 84 cases"])

TICKETS = T
