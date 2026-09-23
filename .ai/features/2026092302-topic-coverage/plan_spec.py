# python3 scripts/gen_plan.py .ai/features/2026092302-topic-coverage .ai/features/2026092302-topic-coverage/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="suggest-api", title="Untagged questions are listable, suggestible and no longer silent",
         requirements=["US-01", "US-02", "US-03"], risk="medium",
         demo=["POST /questions/search {has_topic:false} → 102 câu",
               "POST /questions/suggest-topics → 3 gợi ý kèm điểm và nguồn cho mỗi câu",
               "Tải lại một đề mà máy không phân loại được → câu vào hàng chờ duyệt, không auto_approved"],
         in_scope=["has_topic filter", "suggest endpoint", "ingestion api + adapter", "needs_review rule", "per-document count"]),
    dict(id="UOW-02", slug="tagging-queue", title="The tagging queue clears the backlog",
         requirements=["US-01", "US-03"], risk="medium",
         demo=["Duyệt câu hỏi › Chưa gắn chuyên đề: chọn gợi ý bằng phím 1/2/3, số còn lại giảm",
               "Chọn nhiều câu → Gán chuyên đề cho N câu"],
         in_scope=["queue screen", "suggestion chips", "TopicPicker fallback", "bulk apply", "remaining counter"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="has_topic filter and the per-document count", layer="api", estimate="3h",
  verifies=["AC-01", "AC-05"],
  tests=[f"{API}/tests/test_topic_coverage.py", f"{API}/tests/test_bank_facets.py"],
  touches=[f"{M}/bank/infrastructure/read_models.py", f"{M}/bank/interface/schemas.py"],
  context="", done_when=["has_topic filters the search", "Untagged count per document"])
t(id="T-01-02", uow="UOW-01", title="Suggestion endpoint reusing the ingestion rules", layer="api", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-02"], assumptions=["A-01", "A-05"],
  tests=[f"{API}/tests/test_topic_coverage.py", f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/ingestion/application/api.py", f"{M}/bank/domain/ports.py", f"{M}/bank/application/queries/suggest_topics.py",
           f"{M}/bank/infrastructure/adapters/suggestions.py", f"{M}/bank/interface/router.py", f"{API}/app/main.py"],
  context="ADR-01, ADR-03.", done_when=["Three candidates with score and source", "≤50 ids per request", "Layer rules stay green"])
t(id="T-01-03", uow="UOW-01", title="An unclassified question waits for review", layer="api", estimate="3h",
  depends_on=["T-01-02"], verifies=["AC-04"], assumptions=["A-02"],
  tests=[f"{API}/tests/test_topic_suggest.py", f"{API}/tests/test_documents_api.py"],
  touches=[f"{M}/ingestion/application/stages/topic_suggest.py", f"{M}/ingestion/application/commands/ingest_document.py"],
  context="ADR-02.", done_when=["needs_review when no topic", "Reason in the document log", "Golden numbers unchanged"])
t(id="T-02-01", uow="UOW-02", title="Queue screen with suggestions and keyboard flow", layer="web", estimate="4h",
  depends_on=["T-01-02"], verifies=["AC-01", "AC-02"], assumptions=["A-03"],
  tests=[f"{S}/__tests__/tagging-queue.test.tsx"],
  touches=[f"{S}/services/question.service.ts", f"{S}/hooks/react-query/use-query-question.ts",
           f"{S}/hooks/page-hooks/tagging-queue/use-tagging-queue.tsx",
           f"{S}/components/page-components/TaggingQueue/TaggingQueuePage.tsx", f"{S}/lib/common/nav.ts"],
  context="", done_when=["Suggestions as buttons", "1/2/3 picks", "Remaining count"])
t(id="T-02-02", uow="UOW-02", title="Bulk apply and the live backlog cleared", layer="web", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-03", "AC-05"], assumptions=["A-04"],
  tests=[f"{S}/__tests__/tagging-queue.test.tsx"],
  touches=[f"{S}/components/page-components/TaggingQueue/BulkTopicBar/BulkTopicBar.tsx"],
  context="", done_when=["One request per bulk apply", "Counter drops", "Backlog worked through on the live stack"])
TICKETS = T
