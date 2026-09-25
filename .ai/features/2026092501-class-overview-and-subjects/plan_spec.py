# python3 scripts/gen_plan.py .ai/features/2026092501-class-overview-and-subjects .ai/features/2026092501-class-overview-and-subjects/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="attempt-history", title="Một học sinh đã làm gì, lúc nào, mất bao lâu",
         requirements=["US-01"], risk="low",
         demo=["Mở hồ sơ một học sinh: danh sách lượt làm bài với đề, giờ bắt đầu, giờ nộp, số phút, điểm",
               "Một lượt bị tự nộp vẫn nằm đó và mang dấu riêng"],
         in_scope=["attempts search read model", "duration on read", "history on the student profile"]),
    dict(id="UOW-02", slug="class-overview", title="Nhìn được cả lớp ngay trên trang lớp",
         requirements=["US-02", "US-04"], risk="low",
         demo=["Mở một lớp, chuyển sang tab Tổng quan: bài giao, đã nộp, điểm trung bình, phổ điểm, chuyên đề yếu",
               "Lớp chưa ai nộp thì nói chưa có dữ liệu, không hiện số 0",
               "Menu Lớp & học sinh theo thứ tự Năm học, Cơ cấu trường, Lớp học, Người dùng"],
         in_scope=["class summary read model", "tabs on the class page", "nav order"]),
    dict(id="UOW-03", slug="subject-scoped-reports", title="Báo cáo còn đọc được khi có nhiều môn",
         requirements=["US-03"], risk="low",
         demo=["Báo cáo mặc định vẫn là mọi môn, chọn được một môn",
               "Ở mọi môn, các mạch kiến thức nhóm dưới môn của chúng"],
         in_scope=["subject picker on reports", "grouping by subject in the topic tree"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Read model liệt kê lượt làm bài", layer="api", estimate="4h",
  verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-02", "A-09"],
  tests=[f"{API}/tests/test_assignments_api.py", f"{API}/tests/unit/test_assessment_handlers.py"],
  touches=[f"{M}/assessment/infrastructure/read_models.py",
           f"{M}/assessment/application/queries/search_attempts.py",
           f"{M}/assessment/application/dto.py",
           f"{M}/assessment/interface/schemas.py",
           f"{M}/assessment/interface/deps.py",
           f"{M}/assessment/interface/router.py"],
  context="ADR-01, ADR-02. POST /attempts/search theo hợp đồng list; số phút tính lúc đọc, null khi chưa nộp. "
          "Phạm vi do actor quyết: học sinh bị ép về chính mình, đây đúng chỗ F20 đã vấp.",
  done_when=["Trả về đề, giờ bắt đầu, giờ nộp, số phút, điểm", "Lượt tự nộp có dấu riêng",
             "Học sinh không đọc được lượt của bạn khác"])
t(id="T-01-02", uow="UOW-01", title="Lịch sử làm bài trên hồ sơ học sinh", layer="web", estimate="3h",
  depends_on=["T-01-01"], verifies=["AC-01", "AC-02"], assumptions=["A-01", "A-03"],
  tests=[f"{S}/__tests__/student-record.test.tsx"],
  touches=[f"{S}/components/page-components/StudentRecord/AttemptHistory/AttemptHistory.tsx",
           f"{S}/components/page-components/StudentRecord/StudentRecordPage.tsx",
           f"{S}/hooks/react-query/use-query-attempts.ts",
           f"{S}/services/attempt.service.ts",
           f"{S}/interfaces/attempt.interface.ts"],
  context="Cột thời gian nói rõ là 'từ lúc bắt đầu đến lúc nộp', không phải tổng thời gian từng câu. "
          "Trên dữ liệu seed mọi lượt sẽ là 0 phút và đó là đúng (A-03).",
  done_when=["Bảng có đề, bắt đầu, nộp, số phút, điểm", "Lượt tự nộp nhìn ra được", "Chưa có lượt nào thì nói rõ"])
t(id="T-02-01", uow="UOW-02", title="Read model tổng quan một lớp", layer="api", estimate="4h",
  verifies=["AC-03", "AC-04"], assumptions=["A-05"],
  tests=[f"{API}/tests/test_analytics_api.py", f"{API}/tests/unit/test_analytics_handlers.py"],
  touches=[f"{M}/analytics/infrastructure/read_models.py",
           f"{M}/analytics/application/queries/class_summary.py",
           f"{M}/analytics/application/dto.py",
           f"{M}/analytics/interface/schemas.py",
           f"{M}/analytics/interface/deps.py",
           f"{M}/analytics/interface/router.py"],
  context="ADR-03. Một lời gọi thay vì N+1; phổ điểm đúng mười cột như báo cáo bài giao để hai màn hình không vẽ "
          "hai hình khác nhau từ cùng dữ liệu. Lớp rỗng là rỗng có cấu trúc, không phải lỗi.",
  done_when=["Bài giao, đã nộp, trung bình, phổ điểm, chuyên đề yếu", "Lớp rỗng trả về rỗng chứ không lỗi",
             "Lớp của tổ chức khác là NotFound"])
t(id="T-02-02", uow="UOW-02", title="Tab Học sinh và Tổng quan trên trang lớp", layer="web", estimate="4h",
  depends_on=["T-02-01"], verifies=["AC-03", "AC-04"], assumptions=["A-04"],
  tests=[f"{S}/__tests__/class-detail.test.tsx"],
  touches=[f"{S}/components/page-components/ClassDetail/ClassSummary/ClassSummary.tsx",
           f"{S}/components/page-components/ClassDetail/ClassDetailPage.tsx",
           f"{S}/hooks/page-hooks/class-detail/use-class-detail-page.ts"],
  context="A-04: tab thứ hai cạnh danh sách học sinh, không phải trang mới.",
  done_when=["Chuyển được giữa hai tab", "Tổng quan hiện đủ bốn nhóm số", "Lớp rỗng nói chưa có dữ liệu"])
t(id="T-02-03", uow="UOW-02", title="Thứ tự menu Lớp & học sinh", layer="web", type="chore", estimate="1h",
  verifies=["AC-07"], assumptions=["A-08"],
  tests=[f"{S}/__tests__/nav.test.ts"],
  touches=[f"{S}/lib/common/nav.ts"],
  context="Năm học, Cơ cấu trường, Lớp học, Người dùng — lập lớp trước rồi mới xếp người vào.",
  done_when=["Đúng thứ tự", "Có test ghim thứ tự"])
t(id="T-03-01", uow="UOW-03", title="Chọn môn ở báo cáo, mặc định không đổi", layer="web", estimate="4h",
  verifies=["AC-05", "AC-06"], assumptions=["A-06", "A-07"],
  tests=[f"{S}/__tests__/reports.test.tsx"],
  touches=[f"{S}/components/page-components/Reports/ReportsPage.tsx",
           f"{S}/components/page-components/Reports/TopicStatsTree/TopicStatsTree.tsx",
           f"{S}/hooks/page-hooks/reports/use-reports-page.ts"],
  context="ADR-04. API đã nhận subject_id từ lâu; web chưa bao giờ gửi. Mặc định giữ 'Mọi môn' vì đổi mặc định là "
          "đổi nghĩa con số mà không ai được báo. Danh sách môn lấy từ /api/taxonomy, cùng chỗ ngân hàng lấy.",
  done_when=["Mặc định vẫn là mọi môn", "Chọn một môn thì chỉ còn môn ấy",
             "Ở mọi môn các mạch nhóm dưới môn của chúng"])

TICKETS = T
