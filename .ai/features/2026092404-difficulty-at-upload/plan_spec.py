# python3 scripts/gen_plan.py .ai/features/2026092404-difficulty-at-upload .ai/features/2026092404-difficulty-at-upload/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="rule-and-trace", title="Quy tắc vị trí và dấu vết mức độ",
         requirements=["US-01", "US-02"], risk="medium",
         demo=["Câu Phần I số 1 ra nb, Phần III ra vd — thuần, không cần model",
               "Người đặt mức độ thì dấu vết là manual; lệnh máy không đổi được nó"],
         in_scope=["difficulty_source column", "position rule", "manual is untouchable"]),
    dict(id="UOW-02", slug="model-pass", title="Lượt model trong pipeline tách đề",
         requirements=["US-01"], risk="medium",
         demo=["Tải một đề lên: tách xong mọi câu đều có mức độ",
               "Tắt model: đề vẫn tách xong, mọi câu vẫn có mức độ, nhật ký có cảnh báo"],
         in_scope=["difficulty prompt", "pipeline stage", "graceful degradation"]),
    dict(id="UOW-03", slug="measure-backfill", title="Đo trước khi tin, rồi điền cho câu cũ",
         requirements=["US-03"], risk="medium",
         demo=["Báo cáo: độ phủ của model, đồng thuận với quy tắc vị trí, phân bố hai bên",
               "Lệnh điền: chỉ chạm câu rỗng, chạy lại không đổi gì thêm"],
         in_scope=["difficulty_report.py", "backfill command"]),
    dict(id="UOW-04", slug="review-ui", title="Thấy và sửa được mức độ ngay chỗ đang duyệt",
         requirements=["US-04"], risk="low",
         demo=["Thẻ duyệt hiện mức độ và nói rõ máy gán hay người đặt, sửa ngay tại đó"],
         in_scope=["difficulty on the review card", "provenance shown", "edit in place"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Cột difficulty_source", layer="data", estimate="2h",
  verifies=["AC-04"], assumptions=["A-04"],
  tests=[f"{API}/tests/test_schema_drift.py", f"{API}/tests/test_bank_api.py"],
  touches=[f"{API}/migrations/versions", f"{API}/app/shared/infrastructure/schema/bank.py",
           f"{M}/bank/domain/entities.py", f"{M}/bank/infrastructure/orm.py"],
  context="ADR-01. Nullable cho dòng cũ; soi theo question_topics.source.",
  done_when=["Migration up và down", "alembic check sạch", "Nằm trong snapshot lịch sử"])
t(id="T-01-02", uow="UOW-01", title="Quy tắc vị trí, thuần và kiểm được", layer="domain", estimate="3h",
  verifies=["AC-02"], assumptions=["A-02", "A-05"],
  tests=[f"{API}/tests/unit/test_ingestion_rules.py"],
  touches=[f"{M}/ingestion/domain/services/difficulty_rules.py"],
  context="ADR-02. part + number + type -> mức độ, theo quy ước đề THPT 2025. Không I/O.",
  done_when=["Phủ mọi phần và mọi loại câu", "Không phụ thuộc gì ngoài đầu vào", "Có test cho từng nhánh"])
t(id="T-01-03", uow="UOW-01", title="Mọi đường của người đều ghi manual", layer="api", estimate="3h",
  depends_on=["T-01-01"], verifies=["AC-04"], assumptions=["A-03"],
  tests=[f"{API}/tests/test_bank_api.py", f"{API}/tests/unit/test_bank_handlers.py"],
  touches=[f"{M}/bank/application/commands/create_question.py",
           f"{M}/bank/application/commands/update_question.py",
           f"{M}/bank/application/commands/bulk_update_questions.py"],
  context="ADR-04. Và sửa luôn một lỗ: update_question đặt difficulty mà không gọi check_difficulty.",
  done_when=["Tạo, sửa, hàng loạt đều ghi manual", "check_difficulty chạy trên mọi đường",
             "Hoàn tác khôi phục cả dấu vết"])
t(id="T-02-01", uow="UOW-02", title="Lượt model đoán mức độ", layer="api", estimate="4h",
  depends_on=["T-01-02"], verifies=["AC-02"], assumptions=["A-02"],
  tests=[f"{API}/tests/unit/test_ingestion_rules.py", f"{API}/tests/test_ingest_pipeline.py"],
  touches=[f"{M}/ingestion/domain/services/difficulty_rules.py",
           f"{M}/ingestion/application/difficulty.py"],
  context="Dùng lại hình dạng của TopicModelPass: prompt, chia lô, đọc JSON, tên thắng chỉ số.",
  done_when=["Chia lô như lượt chuyên đề", "Đáp án ngoài bốn mức bị bỏ", "Không import framework nào vào domain"])
t(id="T-02-02", uow="UOW-02", title="Một bước mới trong pipeline", layer="api", estimate="3h",
  depends_on=["T-02-01", "T-01-01"], verifies=["AC-01", "AC-03"], assumptions=["A-01", "A-05"],
  tests=[f"{API}/tests/test_ingest_pipeline.py", f"{API}/tests/test_golden_official.py"],
  touches=[f"{M}/ingestion/application/stages/difficulty_suggest.py",
           f"{M}/ingestion/application/commands/ingest_document.py"],
  context="ADR-02, ADR-03. Model dẫn, quy tắc lấp, độ phủ 100%.",
  done_when=["Không câu nào rỗng sau khi tách", "Model hỏng chỉ là cảnh báo",
             "Bộ 18 đề chuẩn không đổi một con số"])
t(id="T-02-03", uow="UOW-02", title="Câu trắc nghiệm và đúng/sai gửi kèm phương án", layer="api", estimate="3h",
  depends_on=["T-03-01"], verifies=["AC-02"], assumptions=["A-05"],
  tests=[f"{API}/tests/unit/test_ingestion_rules.py", f"{API}/tests/test_ingest_pipeline.py"],
  touches=[f"{M}/ingestion/domain/services/difficulty_rules.py",
           f"{M}/ingestion/application/stages/difficulty_suggest.py",
           f"{API}/scripts/difficulty_report.py"],
  context="T-03-01 đo ra: Phần I lệch ≥2 bậc 47/208, model cao hơn ở 42/47. Prompt chỉ gửi stem, nên model chấm "
          "một câu trắc nghiệm như câu tự giải — không thấy ba phương án nhiễu làm nó dễ đi. Đáp án đúng vẫn "
          "không gửi: nó nói mức độ không còn là mức độ nữa.",
  done_when=["Phương án nằm trong prompt, is_true thì không", "Câu không có phương án giữ nguyên hình cũ",
             "Chạy lại báo cáo và ghi lại con số mới"])
t(id="T-02-04", uow="UOW-02", title="Số câu trong prompt do lượt model tự đặt", layer="api", type="fix", estimate="3h",
  depends_on=["T-02-03"], verifies=["AC-01", "AC-02"], assumptions=["A-02"],
  tests=[f"{API}/tests/unit/test_ingestion_rules.py", f"{API}/tests/unit/test_ingestion_handlers.py",
         f"{API}/tests/test_ingest_pipeline.py"],
  touches=[f"{M}/ingestion/application/difficulty.py",
           f"{M}/ingestion/application/tagging.py",
           f"{M}/ingestion/application/stages/difficulty_suggest.py",
           f"{M}/ingestion/application/stages/topic_suggest.py",
           f"{M}/ingestion/application/api.py",
           f"{API}/scripts/difficulty_report.py"],
  context="Lỗi đo được trên stack thật: số câu THPT lặp lại theo phần (Phần I 1-12, Phần II 1-4, Phần III 1-6), "
          "mà `ask` ghép trả lời bằng {số: khoá} — nên trong một lô, Phần III đè lên Phần II và cả 72 câu Phần II "
          "của 18 đề rơi về quy tắc vị trí. Cùng lỗi ở lượt chuyên đề, nhưng ở đó quy tắc dẫn nên bị che. "
          "Sửa bằng cách để `ask` tự đánh số theo vị trí trong lô, và bỏ số khỏi Row để không caller nào tạo lại "
          "được va chạm — đồng thời thôi rò vị trí câu trong đề vào prompt (ADR-03).",
  done_when=["Row không còn mang số", "Một lô có số câu trùng vẫn nhận đủ trả lời",
             "Phần II nhận mức từ model sau khi tách lại"])
t(id="T-03-01", uow="UOW-03", title="Báo cáo đo hai tín hiệu", layer="api", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-02"], assumptions=["A-05"],
  tests=[f"{API}/tests/unit/test_ingestion_rules.py"],
  touches=[f"{API}/scripts/difficulty_report.py"],
  context="ADR-03, soi theo scripts/suggestion_report.py. Chỉ đọc, không ghi.",
  done_when=["Độ phủ của model", "Đồng thuận model với quy tắc", "Đối chiếu tỉ lệ đúng ở câu đủ 10 lượt"])
t(id="T-03-02", uow="UOW-03", title="Lệnh điền cho câu chưa có mức độ", layer="api", estimate="3h",
  depends_on=["T-02-01", "T-01-03"], verifies=["AC-05"], assumptions=["A-06", "A-03"],
  tests=[f"{API}/tests/test_bank_api.py"],
  touches=[f"{M}/bank/application/commands/backfill_difficulty.py",
           f"{M}/bank/application/dto.py",
           f"{M}/bank/domain/ports.py",
           f"{M}/bank/infrastructure/adapters/suggestions.py",
           f"{M}/bank/infrastructure/repositories.py",
           f"{M}/bank/interface/deps.py",
           f"{M}/bank/interface/schemas.py",
           f"{M}/bank/interface/router.py",
           f"{M}/ingestion/application/api.py",
           f"{API}/app/main.py"],
  context="Chỉ chạm difficulty IS NULL; chạy lại được; org admin. Bán kính thật rộng hơn bản kế hoạch đầu đoán: "
          "quy tắc mức độ sống trong ingestion, nên bank phải hỏi qua application/api.py của nó — thêm một port, "
          "một adapter và một chỗ đăng ký ở composition root, đúng như đường chuyên đề đã đi.",
  done_when=["Chỉ điền câu rỗng", "Chạy lại không đổi gì", "Báo số câu theo từng tín hiệu"])
t(id="T-04-01", uow="UOW-04", title="Mức độ trên thẻ duyệt", layer="web", estimate="4h",
  depends_on=["T-01-03"], verifies=["AC-06"], assumptions=["A-07"],
  # difficulty_source is required on the interface, so every fixture that builds a ParsedQuestion had to name it
  tests=[f"{S}/components/page-components/ReviewDocument/ReviewQueue/ReviewQueue.test.tsx",
         f"{S}/components/page-components/ReviewDocument/QuestionEditor/QuestionEditor.test.tsx",
         f"{S}/__tests__/review-document.test.tsx", f"{S}/__tests__/tagging-queue.test.tsx",
         f"{S}/__tests__/documents.test.tsx", f"{S}/__tests__/exam-builder.test.tsx",
         f"{S}/__tests__/exam-trial.test.tsx", f"{S}/__tests__/parsed-question.test.tsx",
         f"{S}/__tests__/result.test.tsx"],
  touches=[f"{S}/components/page-components/ReviewDocument/ReviewQueue/ReviewQueue.tsx",
           f"{S}/hooks/page-hooks/review-document/use-review-queue.ts",
           f"{S}/constants/question.constant.ts",
           f"{S}/interfaces/question.interface.ts"],
  context="Chuyên đề đã hiện nguồn kiểu 'gợi ý 60%' — mức độ soi theo đúng cách đó.",
  done_when=["Hiện mức độ và nguồn", "Sửa được ngay tại thẻ", "Sửa xong thì nguồn thành người đặt"])
TICKETS = T
