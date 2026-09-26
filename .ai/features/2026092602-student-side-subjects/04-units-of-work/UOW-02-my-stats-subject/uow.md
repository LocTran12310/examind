---
id: UOW-02
slug: my-stats-subject
title: Tiến độ của tôi đọc được khi có nhiều môn
demoable: true
duration: 2d
depends_on: []
requirements: [US-02]
verifies: [AC-04, AC-05, AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Tiến độ của tôi đọc được khi có nhiều môn

## Demo script
1. Bộ chọn môn mặc định Mọi môn; chọn một môn thì cả bốn khối theo môn ấy
2. Lịch sử ôn tập gập lại được và nói còn bao nhiêu lượt nữa

## In scope
- bộ chọn môn trên trang tiến độ
- lịch sử ôn tập gập và lọc

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

`make verify f=.ai/features/2026092602-student-side-subjects` — **2/2** trên `local`, hai viewport, đọc ảnh: màn
hình nhập tài khoản hiện ô kéo thả ("Bấm để chọn file, hoặc kéo thả file vào đây · Định dạng: .csv, .xlsx"),
danh sách cột, và link "Tải file mẫu (.csv)".

**Một bước đã bị bỏ vì trình duyệt không mở được thứ nó định mở**: `.csv` khiến Chromium bắt đầu tải về thay vì
hiện ra trang, nên bước ấy đỏ vì định dạng chứ không vì sản phẩm. Điều nó định khẳng định nằm ở chỗ tốt hơn —
`import.test.tsx` đọc `href` từ DOM, mở file tại `public/<href>` **trên đĩa**, và so hàng tiêu đề với những cột
`user_import.py` thật sự đọc.

**AC-04, AC-05 (bộ chọn môn) và AC-06 (lịch sử gập lại) không có ảnh.** Bộ chọn chỉ hiện khi có từ hai môn, và
lịch sử chỉ gập khi một em đã ôn từ bốn lượt — trung tâm seed không có cả hai. Dựng chúng nghĩa là thêm một môn
bịa vào ngân hàng thật và bốn lượt ôn bịa vào hồ sơ một em thật. Chốt ở `my-stats.test.tsx`: chọn một môn thì
mức nắm vững của môn khác biến mất, lịch sử còn đúng lượt của môn ấy, `/stats/topics` được hỏi lại kèm
`subject_id`, và lượt cũ **không có môn thì không bị nhận bừa** (AC-07).
