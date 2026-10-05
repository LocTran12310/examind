# Mức độ được gán ngay lúc tách đề

## Problem
Đếm trên ngân hàng thật: **376/378 câu không có mức độ nào**. Hệ quả đã thấy ở F21 — mọi dòng ma trận chọn "Mức
độ" đều ra rỗng, và giáo viên chỉ biết sau khi đã dựng xong dòng ấy.

Nguyên nhân: **pipeline tách đề chưa bao giờ chạm vào trường này**. `draft_of` dựng câu hỏi với mười mấy trường,
không có `difficulty`; không một quy tắc, model hay thống kê nào trong repo từng đặt nó. Nó chỉ được đặt bằng tay,
qua form sửa câu hoặc thanh công cụ của ngân hàng.

Loc Tran (chat, 2026-09-24): *"Làm luôn phân mức độ lúc upload đi"* — gán thẳng, có dấu vết là máy gán, lấy tín
hiệu từ model AI và từ vị trí câu trong đề.

## Outcome
---
feature: difficulty-at-upload
slug: 2026092404-difficulty-at-upload
owner: Loc Tran
created: 2026-09-24
status: approved
---

## Success signal
Tải một đề lên, tách xong là mọi câu đều có mức độ, và mỗi câu nói được mức độ ấy do máy đoán hay do người đặt.
Một dòng ma trận "Trắc nghiệm · Nhận biết" trả về một con số khác 0.

## Out of scope
- Sửa mức độ bằng **số liệu làm bài thật** (tỉ lệ đúng). Đó là thứ duy nhất *đo* được độ khó, nhưng cần học sinh
  làm đủ nhiều trước; Loc Tran chốt để sau. Tiền lệ cho việc thống kê ghi ngược vào câu hỏi đã có: `key_audit`.
- Đọc mức độ từ chính văn bản đề (không đề nào trong 18 đề mẫu ghi mức độ)
- Đổi thang mức độ (`nb` / `th` / `vd` / `vdc` giữ nguyên)

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Giáo viên soạn đề | Dòng ma trận chọn mức độ luôn ra 0 | Mức độ có sẵn, ma trận lọc được ngay |
| Giáo viên duyệt câu | Không sửa được mức độ ở hàng đợi duyệt | Sửa được ngay chỗ đang duyệt, và thấy cái nào máy gán |
| Người đọc số liệu | Không phân biệt được máy đoán hay người đặt | Mỗi câu nói rõ mức độ này do đâu mà có |

## Constraints
| Kind | Detail |
| --- | --- |
| Data | Một migration: chỗ ghi mức độ này do đâu mà có |
| Behaviour | Máy **không bao giờ** đè lên mức độ một người đã đặt |
| Quality | Đo trước khi tin: có báo cáo độ phủ và độ đồng thuận giữa hai tín hiệu, như `suggestion_report.py` đã làm cho chuyên đề |
| Ingestion | Bộ 18 đề chuẩn không được đổi một con số nào |
