---
feature: difficulty-at-upload
blocking_open: 0
---

# Assumption register

| ID | Assumption | Confidence | Blocking | Blast radius if wrong | Status | Resolution |
| ---- | --- | --- | --- | --- | --- | --- |
| A-01 | Mức độ được **gán thẳng** lúc tách đề, kèm dấu vết nói rõ do máy gán | high | yes | Ngân hàng, ma trận | confirmed | Loc Tran chọn trong chat (2026-09-24) |
| A-02 | Hai tín hiệu: model của tổ chức, và vị trí câu trong đề (Phần I/II/III + số thứ tự). Không dùng số liệu làm bài | high | yes | Ingestion | confirmed | Loc Tran chọn trong chat (2026-09-24) |
| A-03 | Máy không bao giờ đè lên mức độ mà một người đã đặt — `manual` là bất khả xâm phạm | high | yes | Ngân hàng | confirmed | Accepted under blanket pre-approval; đây là điều kiện để "gán thẳng" không phá công của giáo viên |
| A-04 | Dấu vết là một cột mới trên `questions` (`auto` / `ai` / `manual`), soi theo đúng cách `question_topics.source` đang làm | high | no | Dữ liệu | confirmed | Accepted under blanket pre-approval; chuyên đề đã có đúng khái niệm này và nó đang dùng được |
| A-05 | Quy tắc vị trí là một **quy ước** của đề THPT 2025, không phải sự thật về một câu cụ thể: nó lấp chỗ model không trả lời, và nhường model khi model trả lời | medium | no | Chất lượng | confirmed | Accepted under blanket pre-approval — **và phải đo trước khi chốt ai dẫn**; con số đo được ghi vào review cuối |
| A-06 | Có lệnh điền cho các câu đã có sẵn mà chưa có mức độ, chạy được nhiều lần và chỉ chạm câu đang rỗng | high | no | Ngân hàng | confirmed | Accepted under blanket pre-approval; không có nó thì 374 câu của Loc Tran vẫn rỗng cho tới khi tải lại đề |
| A-07 | Mức độ sửa được ngay trong hàng đợi duyệt, chỗ giáo viên đang nhìn từng câu | medium | no | Duyệt | confirmed | Accepted under blanket pre-approval; máy đã đặt thì phải sửa được ở chỗ đang xem lại |
