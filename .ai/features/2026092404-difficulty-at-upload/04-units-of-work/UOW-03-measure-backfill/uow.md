---
id: UOW-03
slug: measure-backfill
title: Đo trước khi tin, rồi điền cho câu cũ
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-02, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Đo trước khi tin, rồi điền cho câu cũ

## Demo script
1. Báo cáo: độ phủ của model, đồng thuận với quy tắc vị trí, phân bố hai bên
2. Lệnh điền: chỉ chạm câu rỗng, chạy lại không đổi gì thêm

## In scope
- difficulty_report.py
- backfill command

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-02, AC-05 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
