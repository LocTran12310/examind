---
id: UOW-02
slug: filters-time
title: back-office filter operators and business time zone
demoable: true
duration: 2d
depends_on: []
requirements: [US-02, US-03]
verifies: [AC-02, AC-03]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — back-office filter operators and business time zone

## Demo script
1. Người dùng: Họ tên + Bắt đầu bằng 'nguyen'
2. Tạo lúc = 22/09 finds 00:30 Hà Nội

## In scope
- paging ops
- FilterCell
- timezone module
- lib/datetime

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
