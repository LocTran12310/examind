# Source spec for 04-units-of-work — regenerate with:
#   python3 scripts/gen_plan.py .ai/features/2026092206-school-structure-multi-org .ai/features/2026092206-school-structure-multi-org/plan_spec.py
API = "apps/api"
WEB = "apps/web"

UOWS = [
    dict(id="UOW-01", slug="structure", title="Cấp học › Khối › Lớp › Học sinh",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Create org TrungtamC → Cơ cấu trường shows THCS (6–9) and THPT (10–12)",
               "In trungtama: THPT › Khối 10 → add class 10A2 → select it → add/import students",
               "Delete Khối 10 while it has classes → refused 'còn 2 lớp'",
               "Class dialog on Lớp học shows grades grouped by level"],
         in_scope=["Migration 0012 + seed", "structure service + API", "/org/structure page", "GradeSelect in class form"]),
    dict(id="UOW-02", slug="switch-org", title="Active organisation in the token, header selector",
         requirements=["US-03"], depends_on=["UOW-01"], risk="high",
         demo=["Super admin opens the selector → all orgs → picks Trung tâm A → users/classes of A",
               "Log out and in again → lands in Trung tâm A",
               "Suspend Trung tâm A as super admin → selector no longer offers it; session falls back to system"],
         in_scope=["Migration 0013 memberships", "deps scope from token + membership", "switch-org, /me/orgs", "OrgSwitcher wired"]),
    dict(id="UOW-03", slug="cross-org-members", title="Accounts from other organisations",
         requirements=["US-04"], depends_on=["UOW-02"], risk="high",
         demo=["Org admin of A: Người dùng → 'Thêm tài khoản có sẵn' → ttb / gvlan / Giáo viên → row with badge 'Từ ttb'",
               "gvlan logs in with ttb → switches to A → sees A's classes; is teacher in A",
               "Admin of A removes the membership → gvlan's next request in A is refused, account still works in ttb"],
         in_scope=["link/unlink API", "Per-org role in user lists and checks", "Users page actions"]),
]

T = []
def t(**kw):
    T.append(kw)

t(id="T-01-01", uow="UOW-01", title="Migration 0012: school_levels, grades.school_level_id, classes.grade_id + backfill; seed THCS/THPT",
  layer="data", estimate="3h", verifies=["AC-01", "AC-03"], tests=[f"{API}/tests/test_structure.py"],
  touches=[f"{API}/migrations/versions/0012_school_structure.py", f"{API}/app/models/taxonomy.py", f"{API}/app/models/school_class.py", f"{API}/app/seed/org_template.py"],
  assumptions=["A-01", "A-02", "A-03"], context="ADR-01.", done_when=["Backfill on dev DB", "Seed on org create"])
t(id="T-01-02", uow="UOW-01", title="Structure service + API (levels, grades, tree, class grade_id)",
  layer="api", estimate="4h", depends_on=["T-01-01"], verifies=["AC-02", "AC-04", "AC-06"], tests=[f"{API}/tests/test_structure.py", f"{API}/tests/test_classes_api.py"],
  touches=[f"{API}/app/services/structure.py", f"{API}/app/routers/structure.py", f"{API}/app/services/classes.py", f"{API}/app/schemas/classes.py"],
  assumptions=["A-02", "A-04"], context="Range + dependency checks; tree with counts.", done_when=["409 with counts", "Range check", "Tree counts"])
t(id="T-01-03", uow="UOW-01", title="/org/structure page: tree + contextual DataTable; GradeSelect in class form",
  layer="web", estimate="4h", depends_on=["T-01-02"], verifies=["AC-04", "AC-05", "AC-06"], tests=[f"{WEB}/src/__tests__/structure.test.tsx", f"{WEB}/src/__tests__/classes.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/structure/page.tsx", f"{WEB}/src/components/structure/StructureTree.tsx", f"{WEB}/src/components/structure/GradeSelect.tsx", f"{WEB}/src/components/org/ClassForms.tsx", f"{WEB}/src/lib/nav.ts", f"{WEB}/src/components/structure/StructureForms.tsx"],
  context="Level → grades table, grade → classes table, class → students.", done_when=["Tree", "Three tables", "Grouped grade select"])
t(id="T-02-01", uow="UOW-02", title="Migration 0013 memberships + last_org_id; membership service",
  layer="data", estimate="2h", depends_on=["T-01-01"], verifies=["AC-08"], tests=[f"{API}/tests/test_membership.py"],
  touches=[f"{API}/migrations/versions/0013_memberships.py", f"{API}/app/models/user.py", f"{API}/app/services/membership.py"],
  assumptions=["A-05", "A-06"], context="ADR-02.", done_when=["Backfill one home membership per user"])
t(id="T-02-02", uow="UOW-02", title="Scope from token + membership; auth for the active org; switch-org, /me/orgs",
  layer="api", estimate="4h", depends_on=["T-02-01"], verifies=["AC-07", "AC-08", "AC-09", "AC-10"], tests=[f"{API}/tests/test_membership.py", f"{API}/tests/test_auth_api.py"],
  touches=[f"{API}/app/deps.py", f"{API}/app/services/auth.py", f"{API}/app/routers/auth.py", f"{API}/app/schemas/auth.py"],
  assumptions=["A-07", "A-08", "A-09", "A-11"], context="ADR-03, ADR-04.", done_when=["Every request re-checks", "Super admin all orgs", "Suspended fallback"])
t(id="T-02-03", uow="UOW-02", title="OrgSwitcher lists /me/orgs and switches",
  layer="web", estimate="2h", depends_on=["T-02-02"], verifies=["AC-07"], tests=[f"{WEB}/src/__tests__/shell.test.tsx"],
  touches=[f"{WEB}/src/components/app/OrgSwitcher.tsx", f"{WEB}/src/app/(app)/AppShell.tsx", f"{WEB}/src/lib/types.ts"],
  context="Full reload after switching.", done_when=["Lists orgs", "Switch reloads", "Search when many"])
t(id="T-03-01", uow="UOW-03", title="Per-org roles in user lists and cross-user checks (users, classes, review, assignments, adaptive, stats, orgs counts)",
  layer="api", estimate="4h", depends_on=["T-02-02"], verifies=["AC-13"], tests=[f"{API}/tests/test_membership.py", f"{API}/tests/test_users_api.py", f"{API}/tests/test_assignments_api.py", f"{API}/tests/test_review_api.py", f"{API}/tests/test_stats_api.py", f"{API}/tests/test_practice_api.py"],
  touches=[f"{API}/app/services/users.py", f"{API}/app/services/classes.py", f"{API}/app/services/review.py", f"{API}/app/services/assignments.py", f"{API}/app/services/stats.py", f"{API}/app/services/orgs.py"],
  assumptions=["A-06"], context="Replace User.organization_id/User.role checks with memberships.", done_when=["All call sites", "Tenant isolation test"])
t(id="T-03-02", uow="UOW-03", title="link/unlink API",
  layer="api", estimate="2h", depends_on=["T-03-01"], verifies=["AC-11", "AC-12"], tests=[f"{API}/tests/test_membership.py"],
  touches=[f"{API}/app/routers/users.py", f"{API}/app/services/membership.py", f"{API}/app/schemas/users.py"],
  assumptions=["A-10"], context="Home membership cannot be removed; class memberships in that org removed.", done_when=["Link", "Unlink", "Errors"])
t(id="T-03-03", uow="UOW-03", title="Users page: 'Thêm tài khoản có sẵn', 'Gỡ khỏi tổ chức', home-org badge; admin 'Vào tổ chức'",
  layer="web", estimate="3h", depends_on=["T-03-02", "T-02-03"], verifies=["AC-11", "AC-12"], tests=[f"{WEB}/src/__tests__/users.test.tsx", f"{WEB}/src/__tests__/orgs.test.tsx"],
  touches=[f"{WEB}/src/app/(app)/org/users/page.tsx", f"{WEB}/src/components/org/LinkAccountForm.tsx", f"{WEB}/src/app/(app)/admin/orgs/page.tsx"],
  assumptions=["A-12"], context="", done_when=["Link dialog", "Unlink confirm", "Badge"])

TICKETS = T
