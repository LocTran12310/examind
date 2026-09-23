---
id: UOW-03
slug: builder
title: A blueprint that reads well and a swap the teacher controls
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — A blueprint that reads well and a swap the teacher controls

## Demo script
1. Dòng ma trận nằm gọn một hàng ở màn rộng
2. Đổi câu: chọn từ ngân hàng hoặc để hệ thống chọn

## In scope
- blueprint row layout
- empty-topic message
- swap from the bank

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-06, AC-07 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
