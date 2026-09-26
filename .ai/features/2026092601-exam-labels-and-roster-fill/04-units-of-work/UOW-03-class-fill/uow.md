---
id: UOW-03
slug: class-fill
title: Rót một lớp mới từ một lớp cũ trong một lần bấm
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-08, AC-09, AC-10, AC-11]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Rót một lớp mới từ một lớp cũ trong một lần bấm

## Demo script
1. Hộp Thêm học sinh có hai đường: tìm từng em, và từ một lớp cũ
2. Chọn một lớp cũ: cả danh sách hiện ra, tích sẵn, thêm một lần
3. Em đã ở trong lớp đích được đánh dấu và không tích được

## In scope
- chọn lớp nguồn
- danh sách có tích sẵn
- một lần gọi add_members

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-08, AC-09, AC-10, AC-11 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
