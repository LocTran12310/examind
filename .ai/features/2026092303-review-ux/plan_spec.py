# python3 scripts/gen_plan.py .ai/features/2026092303-review-ux .ai/features/2026092303-review-ux/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="review-state", title="One state per document, and every question reachable",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["POST /review/documents/search lọc review_state=pending → chỉ đề còn việc",
               "POST /review/documents/{id}/questions/search state=approved → đọc lại câu đã duyệt"],
         in_scope=["review_state + pending columns", "document questions by state", "re-decide through the existing command"]),
    dict(id="UOW-02", slug="review-screens", title="The review list and page a teacher can read",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Danh sách: một trạng thái, lọc được, chi tiết đếm nằm trong popover, 'Mẫu kiểm chứng' có giải thích",
               "Trang đề: lọc Cần xem / Đã duyệt / Đã loại / Tất cả, sửa và duyệt lại một câu đã duyệt"],
         in_scope=["list column + filter", "sample renamed and explained", "state filter on the document", "edit and re-decide"]),
    dict(id="UOW-03", slug="exam-weighting", title="The exam states its own weighting",
         requirements=["US-03"], risk="low",
         demo=["Mở đề: điểm từng phần, tổng thô và quy về thang 10, sửa điểm từng câu ngay đó"],
         in_scope=["weighting strip", "per-question points made findable"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="review_state and pending on the document list", layer="api", estimate="3h",
  verifies=["AC-01"], assumptions=["A-01"],
  tests=[f"{API}/tests/test_review_api.py", f"{API}/tests/test_review_queue.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py", f"{M}/bank/interface/schemas.py", f"{M}/bank/application/dto.py"],
  context="ADR-01.", done_when=["Derived state", "Filterable and sortable", "Counts still returned"])
t(id="T-01-02", uow="UOW-01", title="A document's questions by state", layer="api", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-03", "AC-04"], assumptions=["A-03", "A-05"],
  tests=[f"{API}/tests/test_review_queue.py", f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/application/queries/document_questions.py", f"{M}/bank/interface/router.py",
           f"{M}/bank/infrastructure/read_models.py"],
  context="ADR-02. The keyboard queue keeps working on the pending filter.",
  done_when=["state filter incl. all", "Paged", "422 on an unknown state", "Re-decide keeps counts right"])
t(id="T-02-01", uow="UOW-02", title="The review list: one state, a filter, the sample explained", layer="web", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-01", "AC-02"], assumptions=["A-02"],
  tests=[f"{S}/__tests__/review-list.test.tsx"],
  touches=[f"{S}/hooks/page-hooks/review/use-review-page.tsx", f"{S}/components/page-components/Review/ReviewCounts/ReviewCounts.tsx",
           f"{S}/constants/review.constant.ts"],
  context="", done_when=["State column + filter", "Counts in a popover", "Mẫu kiểm chứng explained on screen"])
t(id="T-02-02", uow="UOW-02", title="The document page: filter, read back, edit, re-decide", layer="web", estimate="4h",
  depends_on=["T-01-02", "T-02-01"], verifies=["AC-03", "AC-04", "AC-05"],
  tests=[f"{S}/__tests__/review-document.test.tsx"],
  touches=[f"{S}/components/page-components/ReviewDocument/ReviewQueue/ReviewQueue.tsx",
           f"{S}/hooks/page-hooks/review-document/use-review-document.tsx", f"{S}/services/review.service.ts"],
  context="", done_when=["State filter", "Any question opens and edits", "Re-decide updates the counts", "Keyboard flow intact"])
t(id="T-03-01", uow="UOW-03", title="Weighting strip on the exam", layer="web", estimate="3h",
  verifies=["AC-06"], assumptions=["A-04"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/ExamWeighting/ExamWeighting.tsx",
           f"{S}/hooks/page-hooks/exam-detail/use-exam-detail.tsx"],
  context="", done_when=["Points per part and total", "Says what it becomes on the 10 scale", "Per-question points reachable from there"])
TICKETS = T
