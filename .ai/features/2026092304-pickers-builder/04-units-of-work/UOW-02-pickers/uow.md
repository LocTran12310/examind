---
id: UOW-02
slug: pickers
title: Pickers that start on the suggestion and count questions
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Pickers that start on the suggestion and count questions

## Demo script
1. Nhấn T: cây mở sẵn ở chuyên đề được gợi ý, chưa áp dụng gì
2. Số bên cạnh chuyên đề là số câu hỏi; chuyên đề rỗng hiện 0
3. Chọn 20 câu → Gán theo gợi ý → còn lại giảm, câu không có gợi ý được nêu tên

## In scope
- initial topic
- counts from facets
- gán theo gợi ý
- scrollable paged filter

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
