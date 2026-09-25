---
id: UOW-02
slug: class-overview
title: Nhìn được cả lớp ngay trên trang lớp
demoable: true
duration: 2d
depends_on: []
requirements: [US-02, US-04]
verifies: [AC-03, AC-04, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Nhìn được cả lớp ngay trên trang lớp

## Demo script
1. Mở một lớp, chuyển sang tab Tổng quan: bài giao, đã nộp, điểm trung bình, phổ điểm, chuyên đề yếu
2. Lớp chưa ai nộp thì nói chưa có dữ liệu, không hiện số 0
3. Menu Lớp & học sinh theo thứ tự Năm học, Cơ cấu trường, Lớp học, Người dùng

## In scope
- class summary read model
- tabs on the class page
- nav order

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-03, AC-04, AC-07 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify` — **10/10**, ảnh đã đọc. S1 cho thấy tab "Tổng quan" là tab mặc định với bài giao 6 · 150 lượt đã
nộp · trung bình 6.01 · phổ điểm · năm chuyên đề lớp còn yếu. S2 cho thấy tooltip "6–7 điểm · 28 bài · 19% của
150 bài đã nộp". S3 cho thấy tab "Học sinh" không còn số của lớp.

**AC-04 (lớp chưa ai nộp) không có ảnh**: sáu lớp của trung tâm đều đã có bài nộp, và dựng một lớp rỗng chỉ để
chụp một màn hình trống là thêm rác vào dữ liệu thật. Nó được chứng minh ở `class-detail.test.tsx` — `average:
null` cho ra câu "Chưa có bài nộp nào" và **không** cho ra một hàng số 0.

**AC-07 (thứ tự menu) không có bước trình duyệt**, và lý do nằm trong `07-verification.md`: bảng khẳng định
không nói được "cái này đứng trước cái kia", nên bước ấy chỉ khẳng định ba link tồn tại — đúng cả trước lẫn sau
khi đổi thứ tự. Thứ tự được ghim ở `nav.test.ts`, nơi so được cả mảng.
