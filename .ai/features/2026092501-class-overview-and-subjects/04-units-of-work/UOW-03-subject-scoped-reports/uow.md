---
id: UOW-03
slug: subject-scoped-reports
title: Báo cáo còn đọc được khi có nhiều môn
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-05, AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Báo cáo còn đọc được khi có nhiều môn

## Demo script
1. Báo cáo mặc định vẫn là mọi môn, chọn được một môn
2. Ở mọi môn, các mạch kiến thức nhóm dưới môn của chúng

## In scope
- subject picker on reports
- grouping by subject in the topic tree

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify` — **10/10**, ảnh đã đọc. S5 cho thấy bộ chọn "Môn" với mặc định **"Mọi môn"**, và cây chuyên đề
vẫn có dữ liệu như trước.

**AC-06 (nhóm theo môn) không có ảnh, và không nên có.** Trung tâm này dạy đúng một môn, và với một môn thì màn
hình **cố tình** nhìn y như cũ — không tiêu đề môn nào, vì một tiêu đề lặp lại trên mọi hàng chỉ là tiếng ồn.
Thêm môn thứ hai vào ngân hàng thật chỉ để chụp một tiêu đề là bịa dữ liệu để lấy bằng chứng. Nó được chứng minh
ở `reports.test.tsx`, nơi hai môn dựng được trong ba dòng: ba test cho mặc định không gửi `subject_id`, hai môn
thì nhóm, một môn thì không.
