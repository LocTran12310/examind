---
id: UOW-02
slug: model-pass
title: Lượt model trong pipeline tách đề
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Lượt model trong pipeline tách đề

## Demo script
1. Tải một đề lên: tách xong mọi câu đều có mức độ
2. Tắt model: đề vẫn tách xong, mọi câu vẫn có mức độ, nhật ký có cảnh báo

## In scope
- difficulty prompt
- pipeline stage
- graceful degradation

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
