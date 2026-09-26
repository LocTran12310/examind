---
feature: 2026092602-student-side-subjects
gate: G1
---

# Assumptions

| ID | Assumption | Confidence | Blast radius | Blocking | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| A-01 | Học sinh **chọn môn trước khi tạo** đề ôn tập, và đề mang đúng môn ấy | high | Nút tạo đề ôn | yes | confirmed | Anh chọn trong chat 2026-09-26 giữa ba cách; đây là cách anh chọn |
| A-02 | Trung tâm chỉ có **một môn** thì không hỏi, gửi thẳng môn ấy | high | Nút tạo đề ôn | no | confirmed | Accepted under blanket pre-approval; một bước chọn giữa một lựa chọn là một cú bấm vô nghĩa — nhưng đề vẫn phải mang môn, nên vẫn gửi |
| A-03 | Môn mặc định của bước chọn là môn học sinh **yếu nhất** | medium | Nút tạo đề ôn | no | confirmed | Accepted under blanket pre-approval; đó là môn em ấy cần ôn nhất, và mastery đã biết điều đó. Vẫn đổi được |
| A-04 | "Tiến độ của tôi" dùng **bộ chọn môn** như trang Báo cáo, mặc định "Mọi môn" | high | Trang tiến độ | yes | confirmed | Anh chọn trong chat 2026-09-26; giống F23 ADR-04 — thêm lựa chọn, không đổi mặc định |
| A-05 | Bộ chọn ấy áp cho **cả bốn khối** của trang: mức nắm vững, theo chuyên đề, theo loại câu, lịch sử ôn tập | high | Trang tiến độ | yes | confirmed | Accepted under blanket pre-approval; một bộ chọn chỉ áp cho nửa trang là một cái bẫy đọc số |
| A-06 | Lịch sử ôn tập **gập lại được** và mặc định chỉ hiện vài lượt gần nhất | medium | Trang tiến độ | no | confirmed | Accepted under blanket pre-approval; anh viết "không ẩn được" — thứ thiếu là cách thu nó lại, không phải cách xoá nó đi |
| A-07 | Một đề ôn tập **luôn** thuộc đúng một môn từ nay | high | API | yes | confirmed | Accepted under blanket pre-approval; kế hoạch được dựng trong phạm vi một môn nên mọi câu của nó cùng môn — ghi môn ấy lên đề là ghi lại sự thật, không phải suy đoán |
| A-08 | 95 đề ôn tập cũ **để nguyên không môn** | high | Dữ liệu cũ | no | confirmed | Accepted under blanket pre-approval; suy ngược từ câu hỏi của chúng là đoán hộ quá khứ, và lịch sử ôn tập nói "không rõ môn" thật thà hơn |
