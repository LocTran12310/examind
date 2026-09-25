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
- [ ] All of AC-03, AC-04, AC-07 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
