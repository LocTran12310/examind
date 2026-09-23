---
id: UOW-03
slug: model-suggestions
title: The model suggests where the rules are silent
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06, AC-07]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — The model suggests where the rules are silent

## Demo script
1. Câu không có ứng viên nào từ luật → gợi ý gắn nhãn AI, nằm trong cây chuyên đề của môn
2. Tắt model hoặc model treo → vẫn trả về gợi ý theo luật, model_used=false

## In scope
- model pass in suggest_for
- batching
- degrade on failure
- acceptance measured on the backlog

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-06, AC-07 pass
- [x] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
