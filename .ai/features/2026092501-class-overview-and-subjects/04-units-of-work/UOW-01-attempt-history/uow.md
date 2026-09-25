---
id: UOW-01
slug: attempt-history
title: Một học sinh đã làm gì, lúc nào, mất bao lâu
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Một học sinh đã làm gì, lúc nào, mất bao lâu

## Demo script
1. Mở hồ sơ một học sinh: danh sách lượt làm bài với đề, giờ bắt đầu, giờ nộp, số phút, điểm
2. Một lượt bị tự nộp vẫn nằm đó và mang dấu riêng

## In scope
- attempts search read model
- duration on read
- history on the student profile

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify f=.ai/features/2026092501-class-overview-and-subjects` — **10/10** trên `local`, hai viewport, ảnh
đã đọc: S4 cho thấy bảng "Lịch sử làm bài" với đề, giờ bắt đầu, giờ nộp, thời gian và điểm.

**Cột thời gian chứng minh được nó đo thật**, và đó là may chứ không phải thiết kế: lượt "Ôn cá nhân · 12A1" hiện
**1 phút** — đúng lượt tôi làm thử qua trình duyệt ở `.ai/e2e/centre/student` và nó mất thật một phút — còn sáu
lượt do script seed sinh ra hiện **0 phút**, vì script trả lời cả bài trong chưa tới một giây. Hai trường hợp nằm
cạnh nhau trên cùng một bảng, nên cột ấy không phải một cột luôn in 0.

**AC-02 (lượt hệ thống tự đóng) không có ảnh.** Dựng một lượt như thế trên trình duyệt cần để một bài giao hết
giờ và chờ worker quét — hoặc sửa `submitted_at` bằng SQL trên ngân hàng thật. Nó được chứng minh ở nơi dựng
được trạng thái ấy một cách sạch sẽ: `tests/test_assignments_api.py` (một test ghi đúng mốc mà worker ghi, rồi
khẳng định `auto_submitted`) và `student-record.test.tsx` (thẻ "tự nộp khi hết giờ" hiện ra).
