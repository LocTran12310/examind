---
feature: exam-runner-and-roles
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Khung làm bài giữ một bề rộng cố định cho mọi câu, không phụ thuộc nội dung | high | yes | Màn làm bài | confirmed | Loc Tran nêu trong chat (2026-09-24): "Không center kiểu đó, sẽ bị nhảy layout" |
| A-02 | "Toàn đề" là một chế độ xem thứ hai, xếp dọc cả đề **kèm ô trả lời**, tự lưu như chế độ một câu; chế độ một câu vẫn còn | high | yes | Màn làm bài | confirmed | Loc Tran chọn trong chat (2026-09-24) |
| A-03 | Giáo viên chạy thử đề đã giao trên đúng màn hình của học sinh, có chấm và có đáp án, nhưng **không ghi gì** — không attempt, không fact, không mastery | high | yes | Báo cáo, mastery | confirmed | Loc Tran chọn trong chat (2026-09-24): "Chạy thử, không ghi gì" |
| A-04 | Vai trò lồng nhau: HS ⊂ GV ⊂ Admin, ở cả thanh điều hướng lẫn các endpoint phía học sinh | high | yes | Điều hướng, quyền | confirmed | Loc Tran nêu trong chat (2026-09-24) |
| A-05 | Một giáo viên mở "Bài được giao" thấy đúng bài của chính mình — thường là rỗng — chứ không thấy bài của học sinh | medium | no | Điều hướng | confirmed | Accepted under blanket pre-approval; "xem bài của học sinh" đã là báo cáo bài giao, không phải màn này |
| A-06 | Chạy thử không giới hạn số lần và không có đồng hồ đếm ngược | medium | no | Chạy thử | confirmed | Accepted under blanket pre-approval; nó là bản xem trước có chấm, không phải một lượt thi |
