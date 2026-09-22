# python3 scripts/gen_plan.py .ai/features/2026092212-architecture-refactor .ai/features/2026092212-architecture-refactor/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="foundation-tags", title="Layered foundation and the Tags slice (API + web)",
         requirements=["US-01", "US-02", "US-04"], risk="high",
         demo=["POST /api/tags/search with {filters:{name:{operator:'+',value:'ph'}}} → {data,total,page,limit}",
               "Trang Tags: lọc, sắp xếp, phân trang, tạo/sửa/xoá; bảng tự làm mới (không reloadKey)",
               "lint-imports: every contract kept"],
         in_scope=["shared kernel", "import-linter", "error body + request id", "taxonomy/tags module",
                   "web skeleton: query client, http, search body, keys, eslint boundaries", "Tags page"]),
    dict(id="UOW-02", slug="taxonomy-academic", title="Topics, taxonomy and the academic context",
         requirements=["US-01", "US-02", "US-03"], risk="medium",
         demo=["Cây chuyên đề: thêm, đổi tên, chuyển, xoá", "Năm học: tạo, kỳ, lên lớp", "Lớp học: thêm học sinh"],
         in_scope=["topics", "subjects/grades", "school years + rollover", "classes", "structure", "students"]),
    dict(id="UOW-03", slug="identity", title="Identity: sessions, users, organisations",
         requirements=["US-01", "US-02", "US-03"], risk="high",
         demo=["Đăng nhập, đổi mật khẩu, đổi tổ chức (không reload trang, cache xoá)", "Người dùng: tạo, nhập CSV"],
         in_scope=["auth", "me", "users + import", "orgs + admin", "membership"]),
    dict(id="UOW-04", slug="bank-review", title="Question bank and review",
         requirements=["US-01", "US-02", "US-03"], risk="high",
         demo=["Ngân hàng câu: môn, bộ lọc, chip, facets", "Duyệt câu: hàng đợi, sửa, đáp án"],
         in_scope=["question aggregate", "bank search/facets read model", "review, triage, answer key"]),
    dict(id="UOW-05", slug="ingestion", title="Documents and ingestion",
         requirements=["US-01", "US-02", "US-03"], risk="high",
         demo=["Tải lại 18 đề: báo trùng", "Golden 18 đề giữ nguyên số liệu", "Tạo đề từ tài liệu"],
         in_scope=["documents", "assets", "pipeline domain services + adapters", "ai models", "ingestion settings", "worker"]),
    dict(id="UOW-06", slug="assessment", title="Exams, assignments and attempts",
         requirements=["US-01", "US-02", "US-03"], risk="high",
         demo=["Tạo đề theo ma trận, sắp thứ tự, xem trước", "Giao bài, học sinh làm bài, xem kết quả, chấm tự luận"],
         in_scope=["exams", "assignments", "attempts", "scoring"]),
    dict(id="UOW-07", slug="analytics-cleanup", title="Analytics, audit and removal of the old layout",
         requirements=["US-01", "US-02", "US-03", "US-04"], risk="medium",
         demo=["Báo cáo theo chuyên đề, thống kê cá nhân, luyện tập thích ứng", "Cây thư mục cũ không còn; lint sạch"],
         in_scope=["stats, mastery, adaptive, audit", "delete old folders", "architecture map", "final review"]),
]
T = []


def t(**kw):
    T.append(kw)


# UOW-01
t(id="T-01-01", uow="UOW-01", title="Neutral wording in docs and comments", layer="infra", estimate="1h", verifies=["AC-08"],
  tests=[f"{API}/tests/test_health.py"],
  touches=[".ai/final-review.md", f"{API}/app/services/paging.py", f"{WEB}/src/components/data-table/FilterCell.tsx"],
  context="Conventions read as Examind's own.", done_when=["No other project named in docs, ADRs or comments"])
t(id="T-01-02", uow="UOW-01", title="Shared kernel, error body, request id, import-linter", layer="infra", estimate="4h",
  verifies=["AC-01", "AC-03"], assumptions=["A-01", "A-05"],
  tests=[f"{API}/tests/test_errors.py", f"{API}/tests/test_architecture.py"],
  touches=[f"{API}/app/shared/domain/errors.py", f"{API}/app/shared/application/search.py", f"{API}/app/shared/infrastructure/sql_search.py",
           f"{API}/app/shared/interface/errors.py", f"{API}/app/shared/interface/request_id.py", f"{API}/.importlinter", "scripts/verify.sh"],
  context="ADR-01, ADR-02, ADR-04, ADR-05.", done_when=["Shared layers exist", "Errors answer {code,message,details}", "lint-imports runs in verify"])
t(id="T-01-03", uow="UOW-01", title="taxonomy/tags module in four layers + POST /tags/search", layer="api", estimate="3h",
  depends_on=["T-01-02"], verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-08"],
  tests=[f"{API}/tests/test_tags_api.py", f"{API}/tests/test_tags_subject.py", f"{API}/tests/test_search_contract.py", f"{API}/tests/unit/test_tag_handlers.py"],
  touches=[f"{M}/taxonomy/domain/entities.py", f"{M}/taxonomy/application/commands/create_tag.py", f"{M}/taxonomy/infrastructure/repositories.py",
           f"{M}/taxonomy/interface/router.py"],
  context="ADR-03.", done_when=["Tags CRUD + search through handlers", "Old tags router removed", "Handler unit tests with fake ports"])
t(id="T-01-04", uow="UOW-01", title="Web skeleton: query client, http, search body, keys, lint boundaries", layer="web", estimate="3h",
  verifies=["AC-04"], assumptions=["A-03", "A-06"],
  tests=[f"{S}/lib/common/search-body.test.ts", f"{S}/lib/common/http.test.ts"],
  touches=[f"{S}/lib/common/http.ts", f"{S}/lib/common/query-client.ts", f"{S}/lib/common/search-body.ts",
           f"{S}/constants/react-query-key.constant.ts", f"{WEB}/eslint.config.mjs", f"{S}/__tests__/helpers.tsx"],
  context="ADR-06.", done_when=["QueryClientProvider in the app layout", "Error body parsed", "Boundary lint rules"])
t(id="T-01-05", uow="UOW-01", title="DataTable on React Query + Tags page slice", layer="web", estimate="3h",
  depends_on=["T-01-03", "T-01-04"], verifies=["AC-04", "AC-05"],
  tests=[f"{S}/__tests__/tags.test.tsx", f"{S}/__tests__/data-table.test.tsx"],
  touches=[f"{S}/components/common/DataTable/DataTable.tsx", f"{S}/services/tag.service.ts", f"{S}/hooks/react-query/use-query-tag.ts",
           f"{S}/components/page-components/Tags/TagsPage.tsx"],
  context="", done_when=["Tags page uses service → query hook → page component", "Mutations invalidate TAG_KEYS.ALL"])

# UOW-02
t(id="T-02-01", uow="UOW-02", title="taxonomy: subjects, grades, topics tree", layer="api", estimate="4h", depends_on=["T-01-03"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_topics_api.py", f"{API}/tests/test_taxonomy_seed.py"],
  touches=[f"{M}/taxonomy/application/commands/move_topic.py", f"{M}/taxonomy/infrastructure/read_models.py"],
  context="", done_when=["Topics and taxonomy through handlers", "Old routers removed"])
t(id="T-02-02", uow="UOW-02", title="academic: school years, terms, rollover", layer="api", estimate="4h", depends_on=["T-01-02"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_school_years.py", f"{API}/tests/test_rollover.py"],
  touches=[f"{M}/academic/domain/entities.py", f"{M}/academic/application/commands/rollover.py"],
  context="", done_when=["Years and rollover through handlers"])
t(id="T-02-03", uow="UOW-02", title="academic: classes, structure, students", layer="api", estimate="4h", depends_on=["T-02-02"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_classes_api.py", f"{API}/tests/test_structure.py", f"{API}/tests/test_year_history.py"],
  touches=[f"{M}/academic/application/commands/add_members.py", f"{M}/academic/interface/router.py"],
  context="", done_when=["Classes, structure, student record through handlers"])
t(id="T-02-04", uow="UOW-02", title="Web: topics and structure pages", layer="web", estimate="3h", depends_on=["T-02-01", "T-01-05"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/structure.test.tsx"],
  touches=[f"{S}/components/page-components/Topics/TopicsPage.tsx", f"{S}/services/topic.service.ts"],
  context="", done_when=["Pages on query hooks"])
t(id="T-02-05", uow="UOW-02", title="Web: school years, rollover, classes, student record, year store", layer="web", estimate="4h",
  depends_on=["T-02-03", "T-01-05"], verifies=["AC-04", "AC-05"],
  tests=[f"{S}/__tests__/school-years.test.tsx", f"{S}/__tests__/rollover.test.tsx", f"{S}/__tests__/classes.test.tsx"],
  touches=[f"{S}/stores/common/year.store.ts", f"{S}/components/page-components/SchoolYears/SchoolYearsPage.tsx"],
  context="", done_when=["Year choice in a store", "Pages on query hooks"])

# UOW-03
t(id="T-03-01", uow="UOW-03", title="identity: auth, sessions, me, password", layer="api", estimate="4h", depends_on=["T-01-02"],
  verifies=["AC-01", "AC-06"], tests=[f"{API}/tests/test_auth_api.py", f"{API}/tests/test_auth_service.py"],
  touches=[f"{M}/identity/application/commands/login.py", f"{M}/identity/interface/deps.py"],
  context="Actor dependency replaces OrgScope for migrated modules.", done_when=["Auth through handlers", "Actor dependency"])
t(id="T-03-02", uow="UOW-03", title="identity: users, import, organisations, membership", layer="api", estimate="4h", depends_on=["T-03-01"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_users_api.py", f"{API}/tests/test_import.py", f"{API}/tests/test_orgs_api.py"],
  touches=[f"{M}/identity/application/commands/import_users.py", f"{M}/identity/infrastructure/read_models.py"],
  context="", done_when=["Users/orgs through handlers + search"])
t(id="T-03-03", uow="UOW-03", title="Web: shell, login, password, org switch clears cache", layer="web", estimate="3h",
  depends_on=["T-03-01", "T-01-05"], verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/login.test.tsx", f"{S}/__tests__/shell.test.tsx"],
  touches=[f"{S}/components/layout/AppShell/AppShell.tsx", f"{S}/services/auth.service.ts"],
  context="", done_when=["Org switch without reload, cache cleared"])
t(id="T-03-04", uow="UOW-03", title="Web: users, import, admin pages", layer="web", estimate="3h", depends_on=["T-03-02", "T-03-03"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/users.test.tsx", f"{S}/__tests__/import.test.tsx", f"{S}/__tests__/admin.test.tsx"],
  touches=[f"{S}/components/page-components/Users/UsersPage.tsx", f"{S}/services/user.service.ts"],
  context="", done_when=["Pages on query hooks"])

# UOW-04
t(id="T-04-01", uow="UOW-04", title="bank: question aggregate and commands", layer="api", estimate="4h", depends_on=["T-02-01"],
  verifies=["AC-01", "AC-06"], tests=[f"{API}/tests/test_bank_api.py", f"{API}/tests/test_review_bulk.py"],
  touches=[f"{M}/bank/domain/entities.py", f"{M}/bank/application/commands/update_question.py"],
  context="", done_when=["Question writes through handlers"])
t(id="T-04-02", uow="UOW-04", title="bank: search and facets read model", layer="api", estimate="4h", depends_on=["T-04-01"],
  verifies=["AC-02", "AC-06"], tests=[f"{API}/tests/test_bank_facets.py", f"{API}/tests/test_filter_operators.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py"], context="", done_when=["Search + facets on the search contract"])
t(id="T-04-03", uow="UOW-04", title="bank: review, triage, answer key, key audit", layer="api", estimate="4h", depends_on=["T-04-01"],
  verifies=["AC-01", "AC-06"], tests=[f"{API}/tests/test_review_api.py", f"{API}/tests/test_review_queue.py", f"{API}/tests/test_key_audit.py", f"{API}/tests/test_triage.py"],
  touches=[f"{M}/bank/application/commands/review_question.py"], context="", done_when=["Review through handlers"])
t(id="T-04-04", uow="UOW-04", title="Web: bank list page", layer="web", estimate="4h", depends_on=["T-04-02", "T-02-04"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/bank.test.tsx"],
  touches=[f"{S}/components/page-components/Bank/BankPage.tsx", f"{S}/services/question.service.ts"],
  context="", done_when=["Bank on query hooks"])
t(id="T-04-05", uow="UOW-04", title="Web: question detail/form and review", layer="web", estimate="4h", depends_on=["T-04-03", "T-04-04"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/question-edit.test.tsx", f"{S}/__tests__/review-list.test.tsx"],
  touches=[f"{S}/components/page-components/Review/ReviewPage.tsx"], context="", done_when=["Pages on query hooks"])

# UOW-05
t(id="T-05-01", uow="UOW-05", title="ingestion: pure services to domain, I/O to adapters", layer="api", estimate="4h", depends_on=["T-01-02"],
  verifies=["AC-01", "AC-06"], assumptions=["A-07"],
  tests=[f"{API}/tests/test_mtef.py", f"{API}/tests/test_splitter_thpt.py", f"{API}/tests/test_golden_official.py"],
  touches=[f"{M}/ingestion/domain/services/splitter.py", f"{M}/ingestion/infrastructure/adapters/vector_images.py"],
  context="", done_when=["Golden numbers unchanged"])
t(id="T-05-02", uow="UOW-05", title="ingestion: documents commands/queries + worker", layer="api", estimate="4h", depends_on=["T-05-01", "T-04-01"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_documents_api.py", f"{API}/tests/test_document_duplicates.py"],
  touches=[f"{M}/ingestion/application/commands/upload_document.py", f"{API}/app/worker/main.py"],
  context="", done_when=["Documents through handlers; worker calls commands"])
t(id="T-05-03", uow="UOW-05", title="ingestion: assets, AI models, settings", layer="api", estimate="3h", depends_on=["T-05-01"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_assets_api.py", f"{API}/tests/test_ai_models_api.py"],
  touches=[f"{M}/ingestion/application/commands/save_ai_model.py"], context="", done_when=["Through handlers"])
t(id="T-05-04", uow="UOW-05", title="Web: documents list, detail, upload", layer="web", estimate="4h", depends_on=["T-05-02", "T-01-05"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/documents.test.tsx"],
  touches=[f"{S}/components/page-components/Documents/DocumentsPage.tsx", f"{S}/services/document.service.ts"],
  context="", done_when=["Polling via refetchInterval"])
t(id="T-05-05", uow="UOW-05", title="Web: AI models and processing settings", layer="web", estimate="2h", depends_on=["T-05-03", "T-01-05"],
  verifies=["AC-04"], tests=[f"{S}/__tests__/processing-config.test.tsx", f"{S}/__tests__/ai-models.test.tsx"],
  touches=[f"{S}/services/ai-model.service.ts"], context="", done_when=["Pages on query hooks"])

# UOW-06
t(id="T-06-01", uow="UOW-06", title="assessment: exams", layer="api", estimate="4h", depends_on=["T-04-01"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_exams_api.py", f"{API}/tests/test_exam_from_document.py"],
  touches=[f"{M}/assessment/application/commands/build_exam.py"], context="", done_when=["Exams through handlers"])
t(id="T-06-02", uow="UOW-06", title="assessment: assignments, attempts, scoring", layer="api", estimate="4h", depends_on=["T-06-01", "T-02-03"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_assignments_api.py", f"{API}/tests/test_attempts_api.py", f"{API}/tests/test_scoring.py"],
  touches=[f"{M}/assessment/domain/services/scoring.py"], context="", done_when=["Attempts through handlers"])
t(id="T-06-03", uow="UOW-06", title="Web: exams list and detail", layer="web", estimate="4h", depends_on=["T-06-01", "T-04-04"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/exams.test.tsx", f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/Exams/ExamsPage.tsx", f"{S}/services/exam.service.ts"], context="", done_when=["Pages on query hooks"])
t(id="T-06-04", uow="UOW-06", title="Web: assign, runner, results, student home", layer="web", estimate="4h", depends_on=["T-06-02", "T-06-03"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/assign.test.tsx", f"{S}/__tests__/result.test.tsx"],
  touches=[f"{S}/components/page-components/ExamRunner/ExamRunnerPage.tsx"], context="", done_when=["Pages on query hooks"])

# UOW-07
t(id="T-07-01", uow="UOW-07", title="analytics and audit modules", layer="api", estimate="4h", depends_on=["T-06-02"],
  verifies=["AC-01", "AC-02", "AC-06"], tests=[f"{API}/tests/test_stats_api.py", f"{API}/tests/test_adaptive.py", f"{API}/tests/test_audit_api.py"],
  touches=[f"{M}/analytics/infrastructure/read_models.py", f"{M}/audit/interface/router.py"], context="", done_when=["Through handlers"])
t(id="T-07-02", uow="UOW-07", title="Web: reports, my stats, adaptive", layer="web", estimate="3h", depends_on=["T-07-01", "T-06-04"],
  verifies=["AC-04", "AC-05"], tests=[f"{S}/__tests__/reports.test.tsx", f"{S}/__tests__/practice.test.tsx", f"{S}/__tests__/my-stats.test.tsx"],
  touches=[f"{S}/services/stats.service.ts"], context="", done_when=["Pages on query hooks"])
t(id="T-07-03", uow="UOW-07", title="Remove the old layout, final lint rules, architecture map", layer="infra", estimate="3h",
  depends_on=["T-07-02", "T-05-04", "T-05-05", "T-03-04", "T-02-05", "T-04-05"], verifies=["AC-01", "AC-04", "AC-06", "AC-07", "AC-08"],
  tests=[f"{API}/tests/test_architecture.py", f"{S}/__tests__/architecture.test.ts"],
  touches=[".ai/architecture.md", ".ai/final-review.md"], context="", done_when=["Old folders gone", "Map rewritten", "Full suites + golden pass"])
TICKETS = T
