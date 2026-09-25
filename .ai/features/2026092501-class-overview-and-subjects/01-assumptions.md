---
feature: 2026092501-class-overview-and-subjects
gate: G1
---

# Assumptions

| ID | Assumption | Confidence | Blast radius | Blocking | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| A-01 | "Bao nhiêu phút" là `submitted_at − started_at` (giờ treo tường), không phải tổng `seconds_spent` của từng câu | high | Lịch sử làm bài | yes | confirmed | Accepted under blanket pre-approval; đúng chữ anh viết — "từ lúc start đến lúc nộp". Hai đại lượng khác nhau: `seconds_spent` đo thời gian một câu ở trên màn hình và bị kẹp theo cửa sổ lượt làm (F14 ADR-01), còn cái này đo cả lượt |
| A-02 | Một lượt bị hệ thống tự nộp khi hết giờ vẫn hiện trong lịch sử, có dấu riêng | medium | Lịch sử làm bài | no | confirmed | Accepted under blanket pre-approval; giấu nó đi thì cột thời gian sẽ nói dối về những lượt bỏ dở |
| A-03 | Trên dữ liệu seed mọi lượt sẽ hiện **0 phút**, và đó là đúng | high | Kiểm chứng | no | confirmed | Accepted under blanket pre-approval; script seed trả lời cả bài trong chưa tới một giây, nên hiệu số thật sự bằng 0. Không sửa seed cho số đẹp — một cột thời gian bịa còn tệ hơn một cột thời gian trống |
| A-04 | "Tổng quan cả lớp" là **tab thứ hai** cạnh danh sách học sinh, không phải một trang mới | high | Trang lớp | yes | confirmed | Accepted under blanket pre-approval; anh viết "Chi tiết section thêm tab" |
| A-05 | Tổng quan lớp gồm: số bài giao và số bài đã nộp, điểm trung bình, phổ điểm, và chuyên đề lớp yếu nhất | medium | Trang lớp | yes | confirmed | Accepted under blanket pre-approval; đây là bốn thứ Báo cáo đã trả lời được khi lọc theo lớp, chỉ là đang bắt người ta rời trang để lấy |
| A-06 | Bộ chọn môn ở Báo cáo giữ nguyên lựa chọn **"Mọi môn"** làm mặc định | high | Báo cáo | yes | confirmed | Accepted under blanket pre-approval; đổi mặc định là đổi **nghĩa** của con số trang chủ báo cáo mà không ai được báo. Thêm lựa chọn thì an toàn, đổi mặc định thì không |
| A-07 | Ở "Mọi môn", cây chuyên đề nhóm theo môn thay vì phẳng | high | Báo cáo | no | confirmed | Accepted under blanket pre-approval; đây chính là thứ anh nêu — phẳng thì không biết môn nào với môn nào |
| A-08 | Thứ tự menu mới: Năm học · Cơ cấu trường · Lớp học · Người dùng | high | Điều hướng | no | confirmed | Accepted under blanket pre-approval; đúng thứ tự anh viết |
| A-09 | Lịch sử làm bài đọc được bởi giáo viên và quản trị (trang hồ sơ), và bởi chính học sinh về mình | medium | Quyền | no | confirmed | Accepted under blanket pre-approval; theo đúng quy tắc vai lồng nhau đã chốt ở F20 |
