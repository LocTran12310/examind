# python3 scripts/gen_plan.py .ai/features/2026092401-history-keeps-ids .ai/features/2026092401-history-keeps-ids/plan_spec.py
API = "apps/api"
M = f"{API}/app/modules"
UOWS = [
    dict(id="UOW-01", slug="keep-ids", title="The history keeps the id of a deleted question, and the refusal names it",
         requirements=["US-01", "US-02"], risk="low",
         demo=["Xóa một câu đã có lịch sử → các dòng review_events của nó vẫn giữ nguyên question_id",
               "Hoàn tác lượt sửa có câu đã xóa → từ chối cả lượt và nêu đúng id những câu không phục hồi được",
               "Dòng lịch sử cũ (id đã bị xóa trước migration) vẫn đọc được như trước"],
         in_scope=["drop the foreign key", "name the gone questions", "legacy rows unchanged"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Drop the foreign key on review_events.question_id", layer="data", estimate="2h",
  verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02", "A-04"],
  tests=[f"{API}/tests/test_schema_drift.py", f"{API}/tests/test_bank_api.py"],
  touches=[f"{API}/alembic/versions", f"{API}/app/shared/infrastructure/schema/bank.py"],
  context="ADR-01, ADR-02. Keep the column, its type and its index; only the constraint goes.",
  done_when=["Migration up and down, the downgrade's cost stated in its docstring",
             "alembic check clean", "Deleting a question leaves its events untouched"])
t(id="T-01-02", uow="UOW-01", title="The refusal names the questions it cannot put back", layer="api", estimate="2h",
  depends_on=["T-01-01"], verifies=["AC-03"], assumptions=["A-03"],
  tests=[f"{API}/tests/unit/test_bank_handlers.py", f"{API}/tests/test_bank_api.py"],
  touches=[f"{M}/bank/application/commands/undo_batch.py", f"{M}/bank/domain/services/history.py"],
  context="`gone` is already computed and already goes into fields.question_ids; it stops being empty.",
  done_when=["questions_gone carries the ids", "Whole batch still refused",
             "lost_question kept for rows nulled before the migration, its docstring saying so"])
TICKETS = T
