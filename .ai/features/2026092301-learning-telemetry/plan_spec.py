# python3 scripts/gen_plan.py .ai/features/2026092301-learning-telemetry .ai/features/2026092301-learning-telemetry/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="answer-telemetry", title="Answers carry timing, attempt number and no fact when unanswered",
         requirements=["US-01"], risk="medium",
         demo=["Làm một bài, quay lại một câu, nộp → answer_facts có seconds_spent và first_attempt",
               "Mở bài luyện rồi bỏ dở → hết giờ tự nộp, mastery không đổi"],
         in_scope=["timing columns", "runner reports seconds", "grading skips unanswered", "migration"]),
    dict(id="UOW-02", slug="item-stats", title="Item statistics per question, searchable",
         requirements=["US-02"], risk="medium",
         demo=["Chi tiết câu hỏi: tỉ lệ đúng, đúng ngay lần đầu, độ phân biệt, thời gian trung vị, phương án đã chọn",
               "Lọc ngân hàng câu theo tỉ lệ đúng và số lượt"],
         in_scope=["stats read model", "question detail", "search columns", "key audit on the same model"]),
    dict(id="UOW-03", slug="mastery-rules", title="One weak-topic rule, decay, recompute and a weekly snapshot",
         requirements=["US-03", "US-04"], risk="high",
         demo=["Chuyên đề 2 lượt trả lời → 'chưa đủ dữ liệu', không vào kế hoạch ôn",
               "Rebuild dựng lại đúng số cũ; bảng tuần có dữ liệu sau backfill"],
         in_scope=["weak_topics()", "decay", "rebuild endpoint", "student_topic_week", "weekly job", "backfill"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Timing columns and the grading rule", layer="api", estimate="4h",
  verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02"],
  tests=[f"{API}/tests/test_attempts_api.py", f"{API}/tests/unit/test_assessment_handlers.py"],
  touches=[f"{API}/app/shared/infrastructure/schema/assessment.py", f"{M}/assessment/domain/entities.py",
           f"{M}/assessment/application/common.py", f"{M}/assessment/application/commands/save_answer.py",
           f"{API}/migrations/versions/0017_answer_telemetry.py"],
  context="ADR-01, ADR-02.", done_when=["Columns + migration", "Seconds clamped and accumulated", "No fact for an unanswered question"])
t(id="T-01-02", uow="UOW-01", title="Runner reports seconds per question", layer="web", estimate="3h",
  depends_on=["T-01-01"], verifies=["AC-01"],
  tests=[f"{S}/__tests__/result.test.tsx", f"{S}/__tests__/exams.test.tsx"],
  touches=[f"{S}/hooks/page-hooks/exam-runner/use-exam-runner.ts", f"{S}/services/attempt.service.ts", f"{S}/dtos/attempt.dto.ts"],
  context="", done_when=["Seconds sent with each save", "Returning to a question adds time"])
t(id="T-02-01", uow="UOW-02", title="Item statistics read model and question detail", layer="api", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-03"], assumptions=["A-05"],
  tests=[f"{API}/tests/test_item_stats.py", f"{API}/tests/test_key_audit.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py", f"{M}/bank/application/queries/question_stats.py",
           f"{M}/bank/interface/router.py", f"{M}/bank/domain/services/key_audit.py"],
  context="ADR-03.", done_when=["Stats endpoint", "enough_data below 10 observations", "Key audit reuses the model"])
t(id="T-02-02", uow="UOW-02", title="Search and sort the bank by observed difficulty", layer="api", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-04"],
  tests=[f"{API}/tests/test_item_stats.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py", f"{M}/bank/interface/schemas.py"],
  context="", done_when=["stats_correct_ratio and stats_observations filter and sort"])
t(id="T-02-03", uow="UOW-02", title="Question detail shows the statistics", layer="web", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-03"],
  tests=[f"{S}/__tests__/question-edit.test.tsx"],
  touches=[f"{S}/services/question.service.ts", f"{S}/hooks/react-query/use-query-question.ts",
           f"{S}/components/page-components/BankDetail/QuestionStats/QuestionStats.tsx"],
  context="", done_when=["Numbers with their observation count", "'Chưa đủ dữ liệu' under 10"])
t(id="T-03-01", uow="UOW-03", title="One weak-topic rule and decay", layer="api", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-05", "AC-06"], assumptions=["A-03", "A-04"],
  tests=[f"{API}/tests/unit/test_analytics_handlers.py", f"{API}/tests/test_mastery_api.py", f"{API}/tests/test_adaptive.py"],
  touches=[f"{M}/analytics/domain/services/mastery.py", f"{M}/analytics/domain/services/practice.py",
           f"{M}/analytics/application/common.py"],
  context="ADR-04.", done_when=["weak_topics() used everywhere", "Decay on read and update", "Planner ignores thin topics"])
t(id="T-03-02", uow="UOW-03", title="Recompute endpoint", layer="api", estimate="3h",
  depends_on=["T-03-01"], verifies=["AC-06"], assumptions=["A-07"],
  tests=[f"{API}/tests/test_mastery_rebuild.py"],
  touches=[f"{M}/analytics/interface/router.py", f"{M}/analytics/application/commands/rebuild_mastery.py"],
  context="", done_when=["Org admin only", "Replay reproduces the numbers"])
t(id="T-03-03", uow="UOW-03", title="Weekly mastery snapshot, job and backfill", layer="api", estimate="4h",
  depends_on=["T-03-01"], verifies=["AC-07"], assumptions=["A-06"],
  tests=[f"{API}/tests/test_mastery_weekly.py"],
  touches=[f"{API}/app/shared/infrastructure/schema/analytics.py", f"{M}/analytics/application/commands/snapshot_week.py",
           f"{API}/app/worker/handlers.py", f"{API}/migrations/versions/0018_mastery_week.py"],
  context="", done_when=["Table + migration", "Weekly job", "Backfill from facts", "Series endpoint"])
t(id="T-03-04", uow="UOW-03", title="Untagged questions are visible, not silent", layer="api", estimate="2h",
  depends_on=["T-03-01"], verifies=["AC-05"],
  tests=[f"{API}/tests/test_bank_facets.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py"],
  context="Mastery drops answers on questions with no topic; the bank must show how many there are.",
  done_when=["Facet/count of questions without a topic"])
TICKETS = T
