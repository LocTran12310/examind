# Source spec for 04-units-of-work — regenerate with:
#   python3 scripts/gen_plan.py .ai/features/2026092207-school-years .ai/features/2026092207-school-years/plan_spec.py
API = "apps/api"
WEB = "apps/web"

UOWS = [
    dict(id="UOW-01", slug="years", title="School years with HK1/HK2, header year selector, year-scoped classes",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Năm học: 2026-2027 (đang học) created by backfill with HK1/HK2 dates",
               "Create 2027-2028 → header selector lists both → pick 2027-2028 → Lớp học and Cơ cấu trường are empty",
               "Close 2026-2027, edit a class name in it → 'Lịch sử' shows the change flagged năm đã khóa"],
         in_scope=["Migration 0014 years/terms/class link", "Year service + API + audit read API", "YearSwitcher, Năm học page, HistoryPanel", "Classes/structure filtered by year"]),
    dict(id="UOW-02", slug="history", title="Answers remember year, term and classes; reports by year/term; student record",
         requirements=["US-03", "US-04"], depends_on=["UOW-01"], risk="high",
         demo=["Student in 10A1 submits → her fact has 2026-2027, hk1, [10A1]",
               "Reports: pick 2026-2027 and HK1 → numbers change accordingly",
               "Người dùng → student → Hồ sơ: years, classes, results per topic"],
         in_scope=["Migration 0015 facts snapshot + class_members status", "Stats filters", "Record API + page"]),
    dict(id="UOW-03", slug="rollover", title="Chuyển năm học wizard",
         requirements=["US-05"], depends_on=["UOW-02"], risk="high",
         demo=["Năm học 2026-2027 → Chuyển năm học → 2027-2028: 10A1→11A1, 10A2→11A2, 10A3→11A3",
               "Mark one student ở lại, one chuyển đi → Xác nhận → 11A1 has the others, 10A1 (2027-2028) has the retained one",
               "Run again → nothing duplicated"],
         in_scope=["Rollover service + API", "Wizard page"]),
    dict(id="UOW-04", slug="admin-links", title="Đợt kiểm tra picker; org ↔ user assignment from both admin screens",
         requirements=["US-06"], depends_on=["UOW-01"], risk="medium",
         demo=["Upload: Đợt kiểm tra 'Giữa kỳ 2' → document shows 'Giữa kỳ 2'; bank filter 'Giữa kỳ 2' finds its questions",
               "Tổ chức → select Trung tâm B → members panel → add trungtama/buivanchau as student",
               "Tài khoản → buivanchau → organisations panel lists Trung tâm A and Trung tâm B; remove B; history shows both changes"],
         in_scope=["Exam period helper + pickers", "Membership service refactor + admin endpoints", "Members panel, Tài khoản page, orgs panel"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="Migration 0014: school_years, school_terms, classes.school_year_id + backfill; models",
  layer="data", estimate="2h", verifies=["AC-02"], tests=[f"{API}/tests/test_school_years.py"],
  touches=[f"{API}/migrations/versions/0014_school_years.py", f"{API}/app/models/school_year.py", f"{API}/app/models/school_class.py"],
  assumptions=["A-01", "A-02"], context="ADR-01.", done_when=["Backfill on dev DB", "One active per org"])
t(id="T-01-02", uow="UOW-01", title="Year service + API (CRUD, activate/close/reopen, terms) + audit read API",
  layer="api", estimate="4h", depends_on=["T-01-01"], verifies=["AC-01", "AC-04", "AC-16"], tests=[f"{API}/tests/test_school_years.py", f"{API}/tests/test_audit_api.py"],
  touches=[f"{API}/app/services/school_years.py", f"{API}/app/routers/school_years.py", f"{API}/app/routers/audit.py", f"{API}/app/services/classes.py"],
  assumptions=["A-01", "A-04"], context="ADR-05. Classes/structure accept school_year_id; class create defaults to the active year.", done_when=["Closed year edit audited", "Audit paged per target"])
t(id="T-01-03", uow="UOW-01", title="YearSwitcher + YearProvider, Năm học page, HistoryPanel; classes/structure/class form by year",
  layer="web", estimate="4h", depends_on=["T-01-02"], verifies=["AC-03", "AC-04"], tests=[f"{WEB}/src/__tests__/school-years.test.tsx", f"{WEB}/src/__tests__/classes.test.tsx", f"{WEB}/src/__tests__/structure.test.tsx"],
  touches=[f"{WEB}/src/components/app/YearSwitcher.tsx", f"{WEB}/src/components/app/HistoryPanel.tsx", f"{WEB}/src/app/(app)/org/school-years/page.tsx", f"{WEB}/src/app/(app)/org/classes/page.tsx", f"{WEB}/src/app/(app)/org/structure/page.tsx"],
  assumptions=["A-08"], context="", done_when=["Selector persists per org", "History panel", "Year-scoped lists"])
t(id="T-02-01", uow="UOW-02", title="Migration 0015: class_members status/dates, answer_facts year/term/class_ids + backfill; snapshot at grading",
  layer="data", estimate="3h", depends_on=["T-01-01"], verifies=["AC-05"], tests=[f"{API}/tests/test_year_history.py"],
  touches=[f"{API}/migrations/versions/0015_year_history.py", f"{API}/app/models/exam.py", f"{API}/app/services/attempts.py"],
  assumptions=["A-05", "A-06"], context="ADR-02.", done_when=["Snapshot written", "Backfill"])
t(id="T-02-02", uow="UOW-02", title="Stats by class snapshot, year and term; reports page filters",
  layer="api", estimate="3h", depends_on=["T-02-01"], verifies=["AC-06", "AC-07"], tests=[f"{API}/tests/test_year_history.py", f"{API}/tests/test_stats_api.py", f"{WEB}/src/__tests__/reports.test.tsx"],
  touches=[f"{API}/app/services/stats.py", f"{API}/app/routers/stats.py", f"{WEB}/src/app/(app)/org/reports/page.tsx"],
  context="", done_when=["Moved student counted per year", "Term filter"])
t(id="T-02-03", uow="UOW-02", title="Student record API + Hồ sơ học sinh page",
  layer="web", estimate="3h", depends_on=["T-02-01"], verifies=["AC-08"], tests=[f"{API}/tests/test_year_history.py", f"{WEB}/src/__tests__/student-record.test.tsx"],
  touches=[f"{API}/app/routers/students.py", f"{API}/app/services/record.py", f"{WEB}/src/app/(app)/org/students/[id]/page.tsx"],
  context="Links from users list and class members.", done_when=["Years timeline", "Per-year topic results"])
t(id="T-03-01", uow="UOW-03", title="Rollover service: preview + idempotent commit",
  layer="domain", estimate="4h", depends_on=["T-02-01", "T-01-02"], verifies=["AC-09", "AC-10", "AC-11"], tests=[f"{API}/tests/test_rollover.py"],
  touches=[f"{API}/app/services/rollover.py", f"{API}/app/routers/school_years.py"],
  assumptions=["A-07"], context="ADR-03.", done_when=["Name mapping", "Exceptions", "Idempotent", "Close/activate option"])
t(id="T-03-02", uow="UOW-03", title="Chuyển năm học wizard page",
  layer="web", estimate="4h", depends_on=["T-03-01", "T-01-03"], verifies=["AC-09", "AC-10"], tests=[f"{WEB}/src/__tests__/rollover.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/school-years/[id]/rollover/page.tsx", f"{WEB}/src/components/years/RolloverPlan.tsx"],
  context="Per-class cards, per-student action select, summary, confirm.", done_when=["Edit actions", "Commit", "Result summary"])
t(id="T-04-01", uow="UOW-04", title="Đợt kiểm tra helper, upload + bank + document labels",
  layer="web", estimate="2h", depends_on=["T-01-01"], verifies=["AC-12"], tests=[f"{WEB}/src/__tests__/documents.test.tsx", f"{WEB}/src/__tests__/bank.test.tsx"],
  touches=[f"{WEB}/src/lib/exam-period.ts", f"{WEB}/src/components/documents/UploadForm.tsx", f"{WEB}/src/components/bank/BankFilters.tsx", f"{WEB}/src/components/documents/DocumentList.tsx"],
  assumptions=["A-10"], context="", done_when=["One picker", "Labels"])
t(id="T-04-02", uow="UOW-04", title="Membership service by (actor, org, user); admin org members + accounts endpoints",
  layer="api", estimate="3h", depends_on=["T-01-02"], verifies=["AC-13", "AC-14", "AC-15"], tests=[f"{API}/tests/test_admin_memberships.py", f"{API}/tests/test_membership.py"],
  touches=[f"{API}/app/services/membership.py", f"{API}/app/routers/admin_orgs.py", f"{API}/app/routers/admin_users.py"],
  assumptions=["A-11"], context="ADR-04.", done_when=["Both directions", "Home membership protected"])
t(id="T-04-03", uow="UOW-04", title="Members panel on Tổ chức, Tài khoản page with orgs panel, history panels",
  layer="web", estimate="4h", depends_on=["T-04-02", "T-01-03"], verifies=["AC-13", "AC-14", "AC-15", "AC-16"], tests=[f"{WEB}/src/__tests__/admin-members.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/admin/orgs/page.tsx", f"{WEB}/src/app/(app)/admin/users/page.tsx", f"{WEB}/src/components/admin/MembershipTable.tsx", f"{WEB}/src/lib/nav.ts"],
  assumptions=["A-11"], context="", done_when=["Org → users", "User → orgs", "History"])

TICKETS = T
