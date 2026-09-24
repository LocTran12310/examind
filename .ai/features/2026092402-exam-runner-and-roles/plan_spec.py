# python3 scripts/gen_plan.py .ai/features/2026092402-exam-runner-and-roles .ai/features/2026092402-exam-runner-and-roles/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="runner", title="Khung làm bài đứng yên và xem được cả đề",
         requirements=["US-01", "US-02"], risk="low",
         demo=["Chuyển qua lại mười câu: khung không đổi bề rộng",
               "Bật Toàn đề: cả đề hiện ra, trả lời ngay tại đó, bảng câu đánh dấu đã làm"],
         in_scope=["width fix", "whole-paper mode"]),
    dict(id="UOW-02", slug="roles", title="Vai trò lồng nhau: HS ⊂ GV ⊂ Admin",
         requirements=["US-04"], risk="medium",
         demo=["Đăng nhập giáo viên: thanh điều hướng có cả mục của học sinh",
               "Giáo viên gọi endpoint phía học sinh của chính mình: 200, không phải 403"],
         in_scope=["nav inheritance", "student endpoints accept staff"]),
    dict(id="UOW-03", slug="trial-api", title="Chạy thử đề đã giao, không ghi một dòng nào",
         requirements=["US-03"], risk="medium",
         demo=["GET /assignments/{id}/paper: đề không lộ đáp án",
               "POST /assignments/{id}/trial: có điểm, và đếm attempt/answer_facts không đổi"],
         in_scope=["paper endpoint", "in-memory grading"]),
    dict(id="UOW-04", slug="trial-web", title="Giáo viên ngồi vào ghế học sinh",
         requirements=["US-03"], risk="low",
         demo=["Từ đề đã giao, chọn Làm thử, trả lời, nộp, thấy điểm và đáp án"],
         in_scope=["entry point", "runner in trial mode", "result"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Khung làm bài giữ một bề rộng", layer="web", estimate="2h",
  verifies=["AC-01"], assumptions=["A-01"],
  tests=[f"{S}/__tests__/exam-runner.test.tsx"],
  touches=[f"{S}/components/page-components/ExamRunner/Runner/Runner.tsx"],
  context="mx-auto trên một flex item huỷ stretch. Soát cả những chỗ khác dùng cùng cặp lớp.",
  done_when=["Bề rộng không phụ thuộc nội dung câu", "Các trang khác cùng lỗi được soát và sửa"])
t(id="T-01-02", uow="UOW-01", title="Chế độ Toàn đề", layer="web", estimate="4h",
  depends_on=["T-01-01"], verifies=["AC-02", "AC-03"], assumptions=["A-02"],
  tests=[f"{S}/__tests__/exam-runner.test.tsx"],
  touches=[f"{S}/components/page-components/ExamRunner/Runner/Runner.tsx",
           f"{S}/hooks/page-hooks/exam-runner/use-exam-runner.ts"],
  context="ADR-03. Dùng lại QuestionView + AnswerInput và đúng change() đang có.",
  done_when=["Hai chế độ chuyển qua lại", "Trả lời được ở chế độ toàn đề", "Tự lưu và bảng câu không đổi"])
t(id="T-02-01", uow="UOW-02", title="Điều hướng theo vai trò lồng nhau", layer="web", estimate="2h",
  verifies=["AC-06"], assumptions=["A-04"],
  tests=[f"{S}/__tests__/nav.test.ts"],
  touches=[f"{S}/lib/common/nav.ts"],
  context="ADR-02. roles của một mục nghĩa là vai trò thấp nhất thấy được nó.",
  done_when=["GV thấy mục của HS", "Admin thấy mục của GV", "homeFor giữ nguyên cho từng vai trò"])
t(id="T-02-02", uow="UOW-02", title="Endpoint phía học sinh nhận nhân viên", layer="api", estimate="3h",
  verifies=["AC-07"], assumptions=["A-04", "A-05"],
  tests=[f"{API}/tests/test_assignments_api.py", f"{API}/tests/unit/test_assessment_handlers.py"],
  touches=[f"{M}/assessment/application/queries/my_assignments.py",
           f"{M}/assessment/application/commands/start_attempt.py"],
  context="Vẫn lọc theo actor.user_id: giáo viên thấy bài của chính mình, không phải của học sinh.",
  done_when=["Không còn role != student", "Dữ liệu vẫn của chính người gọi", "Học sinh không đổi hành vi"])
t(id="T-03-01", uow="UOW-03", title="GET /assignments/{id}/paper", layer="api", estimate="3h",
  verifies=["AC-04"], assumptions=["A-03"],
  tests=[f"{API}/tests/test_assignments_api.py"],
  touches=[f"{M}/assessment/application/queries", f"{M}/assessment/interface/router.py",
           f"{M}/assessment/interface/schemas.py"],
  context="ADR-04: dùng lại đúng hàm tước dữ liệu mà GET /attempts/{id} dùng.",
  done_when=["Đáp án và lời giải bị tước", "Thứ tự câu của đề", "staff_actor, org-scoped"])
t(id="T-03-02", uow="UOW-03", title="POST /assignments/{id}/trial — chấm mà không ghi", layer="api", estimate="4h",
  depends_on=["T-03-01"], verifies=["AC-05"], assumptions=["A-03", "A-06"],
  tests=[f"{API}/tests/test_assignments_api.py", f"{API}/tests/unit/test_assessment_handlers.py"],
  touches=[f"{M}/assessment/application/queries", f"{M}/assessment/interface/router.py"],
  context="ADR-01. Dùng scoring.grade; không UnitOfWork, không repository ghi.",
  done_when=["Kết quả cùng hình dạng với result của attempt",
             "Test khẳng định đếm attempts và answer_facts không đổi", "Không commit nào được gọi"])
t(id="T-04-01", uow="UOW-04", title="Làm thử từ đề đã giao", layer="web", estimate="4h",
  depends_on=["T-01-02", "T-03-02"], verifies=["AC-04", "AC-05"], assumptions=["A-03"],
  tests=[f"{S}/__tests__/exam-trial.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/AssignedList/AssignedList.tsx",
           f"{S}/app/(app)/org/assignments/[id]/trial", f"{S}/services/assignment.service.ts",
           f"{S}/hooks/react-query/use-query-assignment.ts"],
  context="Dùng lại Runner ở chế độ chạy thử: không đồng hồ, không tự lưu, nộp thì gọi trial.",
  done_when=["Vào được từ danh sách Đã giao", "Runner dùng lại nguyên vẹn",
             "Kết quả hiện điểm và đáp án", "Màn hình nói rõ đây là bản chạy thử"])
TICKETS = T
