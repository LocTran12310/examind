---
id: UOW-01
slug: exam-labels
title: Đề nói được nó thuộc môn nào, khối nào
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03, AC-12]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Đề nói được nó thuộc môn nào, khối nào

## Demo script
1. Tạo đề mới với môn Toán và khối 11: danh sách hiện 11 ở cột Lớp
2. Mở một đề cũ, chọn môn và khối, số được lưu ngay
3. Ma trận của đề chỉ mở chuyên đề của môn đã chọn

## In scope
- môn và khối ở form tạo đề
- sửa tại chỗ trên trang soạn đề

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-12 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify f=.ai/features/2026092601-exam-labels-and-roster-fill` — **10/10** trên `local`, hai viewport, đọc
từng ảnh. S1 cho thấy panel "Môn và lớp" của đề vừa tạo đọc lại đúng **Toán** và **Lớp 11** từ máy chủ; S2 cho
thấy hàng `E2E · nhãn đề` với cột Lớp là **11** — trước bản sửa cột ấy trống ở cả 36 dòng.

**S2 và S3 phải tách đôi.** Bản đầu gộp "xem cột Lớp" với "xoá đề đi" vào một bước, và ảnh chụp lấy **sau** khi
xoá: khẳng định xanh, ảnh là một bảng rỗng, không thấy cái ô `11` mà bước tự nhận là đang chứng minh.

**AC-03 không có ảnh** vì đề vừa tạo chưa có câu nào nên câu cảnh báo **cố tình** không hiện; nó được chốt ở
`exam-builder.test.tsx`. **AC-12 (bỏ trống lại được) là lỗi ở tầng máy chủ** và bằng chứng của nó là
`test_exams_api.py`, đã được chứng minh **đỏ trên mã cũ** trước khi xanh trên mã mới.
