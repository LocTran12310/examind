# python3 scripts/gen_plan.py .ai/features/2026092304-pickers-builder .ai/features/2026092304-pickers-builder/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="bulk-and-guards", title="Bulk by suggestion, subject and grade, and a builder that refuses an empty topic",
         requirements=["US-02", "US-03", "US-04"], risk="medium",
         demo=["POST /questions/bulk/topics với 20 cặp khác nhau → một request, báo số câu bỏ qua",
               "POST /questions/bulk đặt môn và lớp cho các câu chưa phân môn",
               "Ma trận đề có dòng chuyên đề rỗng → 422 nói rõ chuyên đề nào"],
         in_scope=["bulk/topics", "subject and grade in bulk", "blueprint empty-topic guard"]),
    dict(id="UOW-02", slug="pickers", title="Pickers that start on the suggestion and count questions",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Nhấn T: cây mở sẵn ở chuyên đề được gợi ý, chưa áp dụng gì",
               "Số bên cạnh chuyên đề là số câu hỏi; chuyên đề rỗng hiện 0",
               "Chọn 20 câu → Gán theo gợi ý → còn lại giảm, câu không có gợi ý được nêu tên"],
         in_scope=["initial topic", "counts from facets", "gán theo gợi ý", "scrollable paged filter"]),
    dict(id="UOW-03", slug="builder", title="A blueprint that reads well and a swap the teacher controls",
         requirements=["US-04"], risk="low",
         demo=["Dòng ma trận nằm gọn một hàng ở màn rộng",
               "Đổi câu: chọn từ ngân hàng hoặc để hệ thống chọn"],
         in_scope=["blueprint row layout", "empty-topic message", "swap from the bank"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="POST /questions/bulk/topics", layer="api", estimate="3h",
  verifies=["AC-03"], assumptions=["A-03"],
  tests=[f"{API}/tests/test_topic_coverage.py", f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/application/commands/bulk_set_topics.py", f"{M}/bank/interface/router.py", f"{M}/bank/interface/schemas.py"],
  context="ADR-02.", done_when=["Pairs applied in one transaction", "skipped reported", "≤200 and subject checked"])
t(id="T-01-02", uow="UOW-01", title="Subject and grade in the bank's bulk edit", layer="api", estimate="2h",
  verifies=["AC-05"], assumptions=["A-04"],
  tests=[f"{API}/tests/test_bank_api.py"],
  touches=[f"{M}/bank/application/commands/bulk_update_questions.py", f"{M}/bank/interface/schemas.py"],
  context="", done_when=["subject_id and grade in set", "Validated like a single update"])
t(id="T-01-03", uow="UOW-01", title="The blueprint refuses an empty topic", layer="api", estimate="3h",
  verifies=["AC-06"], assumptions=["A-05"],
  tests=[f"{API}/tests/test_exams_api.py"],
  touches=[f"{M}/assessment/domain/services/exam_rules.py", f"{M}/assessment/application/commands/build_exam.py"],
  context="", done_when=["422 empty_topic naming the topic and its count", "A row that can be filled still works"])
t(id="T-02-01", uow="UOW-02", title="Pickers: start on the suggestion, count questions", layer="web", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02"],
  tests=[f"{S}/__tests__/tagging-queue.test.tsx", f"{S}/__tests__/review-document.test.tsx"],
  touches=[f"{S}/components/common/TopicPicker/TopicPicker.tsx", f"{S}/components/common/TopicTreeSelect/TopicTreeSelect.tsx",
           f"{S}/hooks/page-hooks/tagging-queue/use-tagging-queue.ts"],
  context="ADR-01.", done_when=["initial topic expanded and focused", "counts are questions", "no child-count number"])
t(id="T-02-02", uow="UOW-02", title="Gán theo gợi ý, and filters that scroll", layer="web", estimate="4h",
  depends_on=["T-01-01", "T-02-01"], verifies=["AC-03", "AC-04"], assumptions=["A-07"],
  tests=[f"{S}/__tests__/tagging-queue.test.tsx"],
  touches=[f"{S}/components/page-components/TaggingQueue/BulkTopicBar/BulkTopicBar.tsx",
           f"{S}/hooks/react-query/use-query-question.ts", f"{S}/components/common/OptionSelect/OptionSelect.tsx"],
  context="", done_when=["One request per page", "Skipped named", "Dropdown scrolls and pages"])
t(id="T-02-03", uow="UOW-02", title="Subject and grade from the bank toolbar", layer="web", estimate="2h",
  depends_on=["T-01-02"], verifies=["AC-05"],
  tests=[f"{S}/__tests__/bank-bulk.test.tsx"],
  touches=[f"{S}/hooks/page-hooks/bank/use-bank-page.tsx", f"{S}/components/page-components/Bank/BulkBar/BulkBar.tsx"],
  context="", done_when=["Môn and Lớp actions", "Counts of the tabs follow"])
t(id="T-03-01", uow="UOW-03", title="Blueprint row layout and the empty-topic message", layer="web", estimate="3h",
  depends_on=["T-01-03", "T-02-01"], verifies=["AC-06"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/BlueprintEditor/BlueprintEditor.tsx"],
  context="", done_when=["One line at desktop width", "Empty topic named before generating"])
t(id="T-03-02", uow="UOW-03", title="Swap a question from the bank", layer="web", estimate="4h",
  depends_on=["T-03-01"], verifies=["AC-07"], assumptions=["A-06"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/SwapQuestionDialog/SwapQuestionDialog.tsx",
           f"{S}/components/page-components/ExamDetail/ExamQuestions/ExamQuestions.tsx"],
  context="ADR-03.", done_when=["Choose from the bank", "Automatic still there", "Points and order kept"])
TICKETS = T
