# python3 scripts/gen_plan.py .ai/features/2026092211-ui-standards .ai/features/2026092211-ui-standards/plan_spec.py
API = "apps/api"
WEB = "apps/web"
UOWS = [
    dict(dod_done=True, id="UOW-01", slug="duplicates", title="Duplicate uploads: check, skip, re-parse, replace, keep both",
         requirements=["US-01"], risk="high", demo=["Upload a reference file again → 'Đã có file giống hệt' → Bỏ qua → nothing stored"],
         in_scope=["check endpoint", "on_duplicate", "upload form choices", "golden runner re-parses"]),
    dict(dod_done=True, id="UOW-02", slug="filters-time", title="Filter operators and business time zone",
         requirements=["US-02", "US-03"], risk="medium", demo=["Người dùng: Họ tên + Bắt đầu bằng 'nguyen'", "Tạo lúc = 22/09 finds 00:30 Hà Nội"],
         in_scope=["paging ops", "FilterCell", "timezone module", "lib/datetime"]),
    dict(dod_done=True, id="UOW-03", slug="order-shadcn", title="Exam order draft, shadcn consistency, preview dialog",
         requirements=["US-04", "US-05"], risk="low", demo=["Sắp xếp thứ tự → swap → Lưu thứ tự (1 request)", "Preview maximised fills the dialog"],
         in_scope=["ExamQuestions", "raw tags → shadcn", "preview body"]),
]
T = []
def t(**kw): T.append(kw)
t(id="T-01-01", uow="UOW-01", title="API check + on_duplicate/replace_id", layer="api", estimate="3h", verifies=["AC-01"],
  tests=[f"{API}/tests/test_document_duplicates.py", f"{API}/tests/test_documents_api.py"],
  touches=[f"{API}/app/services/documents.py", f"{API}/app/routers/documents.py", f"{API}/app/schemas/documents.py", "scripts/golden_live.py"],
  assumptions=["A-01"], context="ADR-03.", done_when=["Check", "Skip/reparse/replace/keep both"])
t(id="T-01-02", uow="UOW-01", title="Upload form: hash, check, per-file choice", layer="web", estimate="3h", depends_on=["T-01-01"], verifies=["AC-01"],
  tests=[f"{WEB}/src/__tests__/documents.test.tsx", f"{WEB}/src/__tests__/processing-config.test.tsx"],
  touches=[f"{WEB}/src/components/documents/UploadForm.tsx"], context="", done_when=["Choices", "Skipped not sent"])
t(id="T-02-01", uow="UOW-02", title="Server operators + business day bounds", layer="api", estimate="3h", verifies=["AC-02", "AC-03"],
  tests=[f"{API}/tests/test_filter_operators.py", f"{API}/tests/test_paging.py", f"{API}/tests/test_school_years.py"],
  touches=[f"{API}/app/services/paging.py", f"{API}/app/core/timezone.py", f"{API}/app/core/config.py", f"{API}/app/services/school_years.py", f"{API}/app/services/classes.py"],
  assumptions=["A-02", "A-03", "A-04"], context="ADR-01, ADR-02.", done_when=["Ops", "422", "Day bounds"])
t(id="T-02-02", uow="UOW-02", title="FilterCell operator menu + lib/datetime", layer="web", estimate="3h", verifies=["AC-02", "AC-03"],
  tests=[f"{WEB}/src/__tests__/data-table.test.tsx", f"{WEB}/src/lib/datetime.test.ts"],
  touches=[f"{WEB}/src/components/data-table/FilterCell.tsx", f"{WEB}/src/lib/datetime.ts", f"{WEB}/src/lib/dates.ts"], context="", done_when=["Menu", "Formatter"])
t(id="T-03-01", uow="UOW-03", title="Exam order draft; preview dialog body", layer="web", estimate="3h", verifies=["AC-04", "AC-06"],
  tests=[f"{WEB}/src/__tests__/exam-builder.test.tsx"], touches=[f"{WEB}/src/components/exams/ExamQuestions.tsx", f"{WEB}/src/app/(app)/org/exams/[id]/page.tsx"],
  assumptions=["A-05"], context="", done_when=["Draft", "Save once", "Preview fills"])
t(id="T-03-02", uow="UOW-03", title="Raw tags → shadcn across app", layer="web", estimate="4h", verifies=["AC-05"],
  tests=[f"{WEB}/src/__tests__/bank.test.tsx", f"{WEB}/src/__tests__/exams.test.tsx", f"{WEB}/src/components/question/QuestionView.test.tsx"],
  touches=[f"{WEB}/src/components/question/QuestionView.tsx", f"{WEB}/src/components/structure/StructureTree.tsx", f"{WEB}/src/components/documents/ProcessingConfig.tsx", f"{WEB}/src/components/reports/Heatmap.tsx"],
  context="", done_when=["No raw controls"])
TICKETS = T
