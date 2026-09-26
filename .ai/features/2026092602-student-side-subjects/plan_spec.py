# python3 scripts/gen_plan.py .ai/features/2026092602-student-side-subjects .ai/features/2026092602-student-side-subjects/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="practice-subject", title="Đề ôn tập mang môn của nó",
         requirements=["US-01"], risk="low",
         demo=["Học sinh bấm Tạo đề ôn tập, chọn môn, đề sinh ra mang đúng môn ấy",
               "Trung tâm một môn thì không hỏi, đề vẫn có môn"],
         in_scope=["subject qua cổng analytics tới exams.subject_id", "bước chọn môn ở nút tạo đề"]),
    dict(id="UOW-02", slug="my-stats-subject", title="Tiến độ của tôi đọc được khi có nhiều môn",
         requirements=["US-02"], risk="low",
         demo=["Bộ chọn môn mặc định Mọi môn; chọn một môn thì cả bốn khối theo môn ấy",
               "Lịch sử ôn tập gập lại được và nói còn bao nhiêu lượt nữa"],
         in_scope=["bộ chọn môn trên trang tiến độ", "lịch sử ôn tập gập và lọc"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Môn đi xuyên cổng analytics tới cái đề", layer="api", estimate="3h",
  verifies=["AC-03"], assumptions=["A-07"],
  tests=[f"{API}/tests/test_practice_api.py", f"{API}/tests/unit/test_analytics_handlers.py"],
  touches=[f"{M}/analytics/domain/ports.py",
           f"{M}/analytics/infrastructure/adapters/assessment.py",
           f"{M}/analytics/application/commands/start_practice.py",
           f"{M}/assessment/application/api.py",
           f"{M}/assessment/application/commands/create_personal_exam.py"],
  context="ADR-01. Kế hoạch đã được dựng trong phạm vi một môn nên môn là dữ kiện đã biết lúc tạo đề; ghi nó lên "
          "exams.subject_id là ghi lại sự thật. Không đụng assign_class_review (ADR-02).",
  done_when=["POST /me/practice kèm subject_id thì đề mang đúng môn ấy",
             "Không kèm thì đề không có môn, như cũ", "Đề ôn của giáo viên giao không đổi gì"])
t(id="T-01-02", uow="UOW-01", title="Bước chọn môn ở nút Tạo đề ôn tập", layer="web", estimate="3h",
  depends_on=["T-01-01"], verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02", "A-03"],
  tests=[f"{S}/__tests__/practice.test.tsx", f"{S}/__tests__/my-stats.test.tsx"],
  touches=[f"{S}/components/common/PracticeButton/PracticeButton.tsx",
           f"{S}/hooks/common/use-practice-button.ts",
           f"{S}/lib/page-libs/my-stats/weakest-subject.ts",
           f"{S}/hooks/page-hooks/my-stats/use-my-stats-page.ts",
           f"{S}/components/page-components/MyStats/MyStatsPage.tsx"],
  context="Nhiều môn thì hỏi, mặc định là môn yếu nhất (A-03); một môn thì gửi thẳng, không hỏi (A-02) — nhưng "
          "vẫn gửi, để đề luôn có môn.",
  done_when=["Nhiều môn thì có bước chọn, mặc định môn yếu nhất", "Một môn thì không hỏi mà vẫn gửi môn",
             "Ngân hàng môn ấy trống thì nói rõ là môn ấy chưa có câu"])
t(id="T-02-00", uow="UOW-02", title="Mức nắm vững và lịch sử ôn tập nói ra môn của từng hàng", layer="api", estimate="3h",
  verifies=["AC-05", "AC-07"], assumptions=["A-05", "A-08"],
  tests=[f"{API}/tests/test_practice_api.py", f"{API}/tests/unit/test_analytics_handlers.py"],
  touches=[f"{M}/analytics/domain/services/mastery.py",
           f"{M}/analytics/domain/value_objects.py",
           f"{M}/analytics/infrastructure/adapters/assessment.py",
           f"{M}/assessment/application/dto.py",
           f"{M}/assessment/infrastructure/read_models.py",
           f"{M}/analytics/application/queries/my_practice.py"],
  context="ADR-03: một bộ chọn chỉ áp cho nửa trang là cái bẫy đọc số tệ nhất. Hai danh sách này ngắn (≤20 lượt, "
          "vài chục chuyên đề) nên chúng chỉ cần NÓI RA môn của từng hàng, còn lọc thì làm ở tầng đọc — rẻ hơn "
          "luồn một bộ lọc qua ba lớp, và còn hiện được môn lên màn hình. TopicNode đã mang subject_id sẵn.",
  done_when=["Mỗi hàng mức nắm vững có subject_id", "Mỗi lượt ôn tập có subject_id",
             "Lượt cũ không có môn thì trả null chứ không đoán"])
t(id="T-02-01", uow="UOW-02", title="Bộ chọn môn kéo cả bốn khối của trang tiến độ", layer="web", estimate="4h",
  depends_on=["T-02-00"], verifies=["AC-04", "AC-05"], assumptions=["A-04", "A-05"],
  tests=[f"{S}/__tests__/my-stats.test.tsx"],
  touches=[f"{S}/components/page-components/MyStats/MyStatsPage.tsx",
           f"{S}/hooks/page-hooks/my-stats/use-my-stats-page.ts",
           f"{S}/interfaces/mastery.interface.ts",
           f"{S}/interfaces/practice.interface.ts",
           f"{S}/__tests__/mastery.test.tsx"],
  context="ADR-03: một bộ chọn chỉ áp cho nửa trang là cái bẫy đọc số tệ nhất bày ra được. /stats/* đã nhận "
          "subject_id từ F23; mastery và lịch sử ôn thì lọc ở tầng đọc.",
  done_when=["Mặc định Mọi môn, số không đổi so với trước", "Chọn một môn thì cả bốn khối theo môn ấy",
             "Cây chuyên đề nhóm theo môn khi đang ở Mọi môn"])
t(id="T-02-02", uow="UOW-02", title="Lịch sử ôn tập gập lại được", layer="web", estimate="2h",
  verifies=["AC-06", "AC-07"], assumptions=["A-06", "A-08"],
  tests=[f"{S}/__tests__/my-stats.test.tsx"],
  touches=[f"{S}/components/page-components/MyStats/PracticeHistory/PracticeHistory.tsx"],
  context="Anh viết 'không ẩn được, không lọc được'. Thu gọn chứ không xoá: đó là dữ liệu học tập của chính em "
          "ấy. Lượt cũ không có môn thì không rơi vào môn nào khi đang lọc, và nói ra điều đó.",
  done_when=["Mặc định chỉ hiện vài lượt và nói còn bao nhiêu", "Mở rộng và thu gọn được",
             "Lượt không rõ môn không bị gán bừa"])

TICKETS = T
