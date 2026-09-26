# python3 scripts/gen_plan.py .ai/features/2026092601-exam-labels-and-roster-fill .ai/features/2026092601-exam-labels-and-roster-fill/plan_spec.py
API = "apps/api"
WEB = "apps/web"
M = f"{API}/app/modules"
S = f"{WEB}/src"
UOWS = [
    dict(id="UOW-01", slug="exam-labels", title="Đề nói được nó thuộc môn nào, khối nào",
         requirements=["US-01"], risk="low",
         demo=["Tạo đề mới với môn Toán và khối 11: danh sách hiện 11 ở cột Lớp",
               "Mở một đề cũ, chọn môn và khối, số được lưu ngay",
               "Ma trận của đề chỉ mở chuyên đề của môn đã chọn"],
         in_scope=["môn và khối ở form tạo đề", "sửa tại chỗ trên trang soạn đề"]),
    dict(id="UOW-02", slug="review-log", title="Ô đề ôn cá nhân nói đủ: đề nào, bao giờ, còn hạn không, mấy đề",
         requirements=["US-02"], risk="low",
         demo=["Tab Tổng quan của lớp: ô của một em hiện tên đề, ngày giao, hạn và trạng thái",
               "Một em quá hạn mà chưa nộp thì nhìn ra ngay",
               "Em được giao ba đề thì ô nói còn 2 đề trước đó"],
         in_scope=["read model trả ngày tháng và số lượt", "ô trên bảng tổng quan lớp"]),
    dict(id="UOW-03", slug="class-fill", title="Rót một lớp mới từ một lớp cũ trong một lần bấm",
         requirements=["US-03"], risk="low",
         demo=["Hộp Thêm học sinh có hai đường: tìm từng em, và từ một lớp cũ",
               "Chọn một lớp cũ: cả danh sách hiện ra, tích sẵn, thêm một lần",
               "Em đã ở trong lớp đích được đánh dấu và không tích được"],
         in_scope=["chọn lớp nguồn", "danh sách có tích sẵn", "một lần gọi add_members"]),
]
T = []


def t(**kw):
    T.append(kw)


t(id="T-01-01", uow="UOW-01", title="Môn và Lớp ở form tạo đề", layer="web", estimate="3h",
  verifies=["AC-01"], assumptions=["A-01", "A-02"],
  tests=[f"{S}/__tests__/exams.test.tsx"],
  touches=[f"{S}/components/page-components/Exams/NewExamForm/NewExamForm.tsx",
           f"{S}/hooks/page-hooks/exams/use-new-exam-form.ts",
           f"{S}/dtos/exam.dto.ts"],
  context="ADR-01. API đã nhận cả hai từ đầu; web chưa bao giờ hỏi. Danh sách môn và khối lấy từ /api/taxonomy, "
          "cùng chỗ ngân hàng lấy. Cả hai không bắt buộc (A-02).",
  done_when=["Tạo được đề kèm môn và khối", "Bỏ trống vẫn tạo được", "Cột Lớp của danh sách hiện số"])
t(id="T-01-02", uow="UOW-01", title="Sửa môn và khối tại chỗ trên trang soạn đề", layer="web", estimate="3h",
  verifies=["AC-02", "AC-03"], assumptions=["A-08"],
  tests=[f"{S}/__tests__/exam-builder.test.tsx"],
  touches=[f"{S}/components/page-components/ExamDetail/ExamLabels/ExamLabels.tsx",
           f"{S}/components/page-components/ExamDetail/ExamDetailPage.tsx",
           f"{S}/hooks/page-hooks/exam-detail/use-exam-detail-page.ts"],
  context="ADR-03. Lưu ngay khi chọn, như PointsByType. Đề đã có câu hỏi thì nói rõ đổi môn chỉ đổi phạm vi ma "
          "trận, câu đã có giữ nguyên — không thêm guard ở API.",
  done_when=["Chọn là lưu, không có nút Lưu riêng", "Ma trận đổi theo môn vừa chọn",
             "Đề đã có câu hỏi thì có câu cảnh báo"])
t(id="T-02-01", uow="UOW-02", title="Read model trả ngày giao, hạn và số lượt ôn cá nhân", layer="api", estimate="4h",
  verifies=["AC-04", "AC-05", "AC-06", "AC-07"], assumptions=["A-03", "A-04"],
  tests=[f"{API}/tests/test_stats_api.py"],
  touches=[f"{M}/assessment/infrastructure/read_models.py",
           f"{M}/assessment/application/dto.py",
           f"{M}/analytics/domain/ports.py",
           f"{M}/analytics/application/queries/class_overview.py",
           f"{M}/analytics/interface/router.py"],
  context="ADR-02. Cùng một truy vấn: lượt mới nhất cộng COUNT tổng số lượt. Đếm ở Python sau limit 1 sẽ luôn "
          "ra 1 — đó là cái bẫy của ticket này.",
  done_when=["Trả tên đề, assignment_id, open_at, close_at, status và tổng số lượt",
             "Chưa giao lần nào thì trả null", "Học sinh của tổ chức khác không lọt vào"])
t(id="T-02-02", uow="UOW-02", title="Ô đề ôn cá nhân trên bảng tổng quan lớp", layer="web", estimate="3h",
  depends_on=["T-02-01"], verifies=["AC-04", "AC-05", "AC-06", "AC-07"], assumptions=["A-04", "A-09"],
  tests=[f"{S}/__tests__/class-detail.test.tsx"],
  touches=[f"{S}/components/page-components/ClassDetail/ClassOverview/ClassOverview.tsx",
           f"{S}/interfaces/mastery.interface.ts"],
  context="Tên đề link sang báo cáo bài giao (A-09). Quá hạn = hạn đã qua và chưa nộp (A-04); đã nộp thì hạn "
          "không còn nghĩa gì để cảnh báo.",
  done_when=["Tên đề, ngày giao, hạn, trạng thái", "Quá hạn mà chưa nộp thì nhìn ra",
             "Nhiều đề thì nói còn mấy đề", "Chưa giao thì nói chưa giao"])
t(id="T-03-01", uow="UOW-03", title="Thêm cả một lớp cũ vào lớp đang mở", layer="web", estimate="4h",
  verifies=["AC-08", "AC-09", "AC-10", "AC-11"], assumptions=["A-05", "A-06", "A-07"],
  tests=[f"{S}/__tests__/classes.test.tsx"],
  touches=[f"{S}/components/page-components/Classes/MemberManager/MemberManager.tsx",
           f"{S}/components/page-components/Classes/MemberManager/FromClass.tsx",
           f"{S}/hooks/page-hooks/classes/use-member-manager.ts"],
  context="ADR-04. Không API mới: POST /classes/{id}/members đã nhận danh sách user_ids. Lớp nguồn lấy từ "
          "POST /classes/search, học sinh lấy từ POST /users/search lọc class_id. Tích sẵn cả lớp (A-05); em đã "
          "ở trong lớp đích bị khoá (A-07). Hộp thoại chỉ sang 'Chuyển năm học' cho trường hợp cả năm (AC-11).",
  done_when=["Chọn lớp cũ thấy cả danh sách, tích sẵn", "Thêm một lần một lời gọi",
             "Bỏ tích được từng em", "Em đã ở trong lớp bị khoá", "Có lối chỉ sang Chuyển năm học"])

TICKETS = T
