---
id: UOW-02
slug: review-log
title: Ô đề ôn cá nhân nói đủ: đề nào, bao giờ, còn hạn không, mấy đề
demoable: true
duration: 2d
depends_on: []
requirements: [US-02]
verifies: [AC-04, AC-05, AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Ô đề ôn cá nhân nói đủ: đề nào, bao giờ, còn hạn không, mấy đề

## Demo script
1. Tab Tổng quan của lớp: ô của một em hiện tên đề, ngày giao, hạn và trạng thái
2. Một em quá hạn mà chưa nộp thì nhìn ra ngay
3. Em được giao ba đề thì ô nói còn 2 đề trước đó

## In scope
- read model trả ngày tháng và số lượt
- ô trên bảng tổng quan lớp

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-04, AC-05, AC-06, AC-07 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify` — **10/10**, ảnh đã đọc. S4 cho thấy ô "Đề ôn cá nhân" của hs001 đọc thành câu: **Ôn cá nhân ·
12A1** (link sang báo cáo bài giao) · **giao 25/09/2026 · hạn 15/10/2026** · **Đã làm**, và các em khác là
**Chưa làm** với đúng ngày ấy.

**Một khẳng định của bước này từng xanh mà không chứng minh gì.** Bản đầu viết `text=Đề ôn cá nhân` và nó xanh
— nhưng xanh nhờ cái **nút "Giao đề ôn cá nhân"** ở góc trên trang, không nhờ ô đang kiểm. Giờ mọi khẳng định
bám vào `[data-testid=ov-hs001]`.

**AC-05, AC-06, AC-07 không có ảnh**: trung tâm seed giao đúng một đề cho mỗi em và hạn chưa qua, nên ba nhánh
kia không tồn tại trong dữ liệu; giao thêm một vòng chỉ để chụp ảnh là thêm 150 bài giao bịa. Cả ba chốt ở
`mastery.test.tsx`, và AC-06 còn chốt ở `test_practice_api.py` — giao hai vòng rồi khẳng định `total == 2`,
đúng chỗ mà đếm sau `limit(1)` sẽ trả lời 1.
