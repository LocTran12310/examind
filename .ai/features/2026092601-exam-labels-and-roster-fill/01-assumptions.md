---
feature: 2026092601-exam-labels-and-roster-fill
gate: G1
---

# Assumptions

| ID | Assumption | Confidence | Blast radius | Blocking | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| A-01 | "Lớp" của một đề là **khối** (10/11/12) lấy từ `taxonomy.grades`, không phải một lớp học cụ thể như 12A1 | high | Danh sách đề | yes | confirmed | Accepted under blanket pre-approval; cột đã tên là "Lớp", lọc `kind: number`, và `exams.grade` là `int` — một lớp cụ thể sẽ là `class_id`, không phải con số này |
| A-02 | Môn và Lớp đều **không bắt buộc** khi tạo đề | medium | Form tạo đề | no | confirmed | Accepted under blanket pre-approval; API để cả hai `None`, và một đề nháp chưa biết dạy khối nào vẫn phải tạo được. Đặt sau ở trang soạn đề |
| A-03 | Ô "Đề ôn cá nhân" hiện **lượt giao gần nhất đầy đủ**, cộng một dòng đếm khi có nhiều hơn một | high | Trang lớp | yes | confirmed | Accepted under blanket pre-approval; liệt kê hết làm bảng 25 dòng cao gấp ba mà câu hỏi thường trực chỉ là "em ấy đang phải làm đề nào" — xem ADR-02 |
| A-04 | "Quá hạn" = `close_at` đã qua **và** em ấy chưa nộp | high | Trang lớp | no | confirmed | Accepted under blanket pre-approval; đã nộp rồi thì hạn không còn nghĩa gì để cảnh báo |
| A-05 | Thêm từ lớp cũ: mặc định **tích sẵn mọi học sinh** của lớp nguồn, bỏ tích được từng em | high | Hộp thêm học sinh | yes | confirmed | Accepted under blanket pre-approval; anh viết "chọn toàn lớp" — mặc định phải là cả lớp, còn bỏ ra vài em là ngoại lệ |
| A-06 | Lớp nguồn chọn được là **mọi lớp khác của tổ chức, mọi năm học**, mới trước | medium | Hộp thêm học sinh | no | confirmed | Accepted under blanket pre-approval; giới hạn vào năm liền trước là đoán: một lớp mới có thể gom từ hai lớp cũ, hoặc từ lớp cùng năm khi tách lớp |
| A-07 | Học sinh đã ở trong lớp đích thì **bỏ qua im lặng**, không phải lỗi | high | Hộp thêm học sinh | no | confirmed | Accepted under blanket pre-approval; `add_members` đã idempotent, và người dùng thêm lần hai vì không chắc lần một xong chưa |
| A-08 | Đổi Môn của một đề **đã có câu hỏi** vẫn cho phép | medium | Trang soạn đề | no | confirmed | Accepted under blanket pre-approval; xem ADR-03 — câu đã có giữ nguyên, môn chỉ đổi phạm vi ma trận, và màn hình nói ra điều đó |
| A-09 | Tên đề ôn cá nhân link sang **báo cáo bài giao** (`/org/assignments/{id}`), không sang trang đề | medium | Trang lớp | no | confirmed | Accepted under blanket pre-approval; người dạy bấm vào để xem em ấy làm ra sao, không phải để sửa đề |
