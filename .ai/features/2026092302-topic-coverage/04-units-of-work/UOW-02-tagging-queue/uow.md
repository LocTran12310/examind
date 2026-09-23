---
id: UOW-02
slug: tagging-queue
title: The tagging queue clears the backlog
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-03]
verifies: [AC-01, AC-02, AC-03, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — The tagging queue clears the backlog

## Demo script
1. Duyệt câu hỏi › Chưa gắn chuyên đề: chọn gợi ý bằng phím 1/2/3, số còn lại giảm
2. Chọn nhiều câu → Gán chuyên đề cho N câu

## In scope
- queue screen
- suggestion chips
- TopicPicker fallback
- bulk apply
- remaining counter

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-05 pass
- [x] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
