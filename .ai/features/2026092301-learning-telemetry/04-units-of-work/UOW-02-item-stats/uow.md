---
id: UOW-02
slug: item-stats
title: Item statistics per question, searchable
demoable: true
duration: 2d
depends_on: []
requirements: [US-02]
verifies: [AC-03, AC-04]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Item statistics per question, searchable

## Demo script
1. Chi tiết câu hỏi: tỉ lệ đúng, đúng ngay lần đầu, độ phân biệt, thời gian trung vị, phương án đã chọn
2. Lọc ngân hàng câu theo tỉ lệ đúng và số lượt

## In scope
- stats read model
- question detail
- search columns
- key audit on the same model

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-03, AC-04 pass
- [x] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
