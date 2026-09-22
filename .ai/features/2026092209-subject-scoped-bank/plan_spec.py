# Source spec for 04-units-of-work — regenerate with:
#   python3 scripts/gen_plan.py .ai/features/2026092209-subject-scoped-bank .ai/features/2026092209-subject-scoped-bank/plan_spec.py
API = "apps/api"
WEB = "apps/web"

UOWS = [
    dict(dod_done=True, id="UOW-01", slug="facets-tags", title="Tags by subject, subject 'none' / school-year filters, facet counts API",
         requirements=["US-02", "US-03", "US-04"], risk="medium",
         demo=["GET /questions/facets?subject_id=<Toán> → topics with subtree counts, types, periods, tags",
               "Create a Toán tag → /tags?subject_id=<Lý> does not list it; source tags listed for both",
               "school_year=2024-2025 keeps only questions from 2024-2025 files"],
         in_scope=["Migration 0016 + backfill", "bank filters", "facets endpoint", "tags API subject"]),
    dict(dod_done=True, id="UOW-02", slug="bank-ui", title="Subject tabs, Bộ lọc sheet with counts, chips; exam matrix and Tags page by subject",
         requirements=["US-01", "US-02", "US-03", "US-04"], depends_on=["UOW-01"], risk="medium",
         demo=["Bank: Toán (396) tab → Bộ lọc → Hàm số + Thi thử + Sở GD&ĐT Ninh Bình → Áp dụng → chips + count; reload keeps it",
               "Switch to Vật lý → topic/tag chips gone, others stay",
               "Exam of Toán → matrix topic picker shows only Toán topics"],
         in_scope=["SubjectTabs, FilterSheet, FilterChips, BankFilters", "Bank page", "Exam page topics/tags", "Tags page subject"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="Migration 0016 tags.subject_id + backfill; tag API with subject and shared",
  layer="data", estimate="3h", verifies=["AC-06", "AC-07"], tests=[f"{API}/tests/test_tags_subject.py"],
  touches=[f"{API}/migrations/versions/0016_tag_subject.py", f"{API}/app/models/taxonomy.py", f"{API}/app/services/tags.py", f"{API}/app/routers/tags.py", f"{API}/app/schemas/taxonomy.py"],
  assumptions=["A-02"], context="ADR-03.", done_when=["Backfill", "Subject + shared listing", "Validation"])
t(id="T-01-02", uow="UOW-01", title="Bank filters subject none / school_year; GET /questions/facets",
  layer="api", estimate="4h", verifies=["AC-03", "AC-05", "AC-09"], tests=[f"{API}/tests/test_bank_facets.py"],
  touches=[f"{API}/app/services/bank.py", f"{API}/app/routers/questions.py"],
  assumptions=["A-04", "A-06"], context="ADR-02.", done_when=["Facets exclude own dimension", "Subtree counts", "School year"])
t(id="T-02-01", uow="UOW-02", title="SubjectTabs + FilterSheet + FilterChips; bank page by subject",
  layer="web", estimate="4h", depends_on=["T-01-02", "T-01-01"], verifies=["AC-01", "AC-02", "AC-03", "AC-04", "AC-05"],
  tests=[f"{WEB}/src/__tests__/bank.test.tsx"],
  touches=[f"{WEB}/src/components/bank/SubjectTabs.tsx", f"{WEB}/src/components/bank/FilterSheet.tsx", f"{WEB}/src/components/bank/FilterChips.tsx", f"{WEB}/src/components/bank/BankFilters.tsx", f"{WEB}/src/app/(app)/org/bank/page.tsx", f"{WEB}/src/components/topics/TopicTreeSelect.tsx", f"{WEB}/src/lib/types.ts"],
  assumptions=["A-01", "A-03", "A-05"], context="ADR-01.", done_when=["Tabs", "Sheet", "Chips", "URL state"])
t(id="T-02-02", uow="UOW-02", title="Exam matrix and Tags page by subject",
  layer="web", estimate="3h", depends_on=["T-01-01"], verifies=["AC-06", "AC-08"], tests=[f"{WEB}/src/__tests__/tags.test.tsx", f"{WEB}/src/__tests__/exams.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/exams/[id]/page.tsx", f"{WEB}/src/app/(app)/org/tags/page.tsx"],
  assumptions=["A-07"], context="", done_when=["Exam matrix", "Tags subject column + form"])

TICKETS = T
