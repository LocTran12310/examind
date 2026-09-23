---
id: UOW-02
slug: review-screens
title: The review list and page a teacher can read
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — The review list and page a teacher can read

## Demo script
1. Danh sách: một trạng thái, lọc được, chi tiết đếm nằm trong popover, 'Mẫu kiểm chứng' có giải thích
2. Trang đề: lọc Cần xem / Đã duyệt / Đã loại / Tất cả, sửa và duyệt lại một câu đã duyệt

## In scope
- list column + filter
- sample renamed and explained
- state filter on the document
- edit and re-decide

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
