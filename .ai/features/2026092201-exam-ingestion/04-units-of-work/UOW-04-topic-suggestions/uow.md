---
id: UOW-04
slug: topic-suggestions
title: Parsed questions carry metadata and a suggested topic
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-06]
verifies: [AC-21, AC-22]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Parsed questions carry metadata and a suggested topic

## Demo script
1. Open the parsed de-mau-toan10 document
2. Each question shows Toán · Lớp 10 · HK1 · Giữa kỳ, source tag, and a suggested topic chip (e.g. 'Hàm số bậc hai và đồ thị' 0.8)
3. With a tagging model configured, re-parse → suggestions marked AI

## In scope
- Keyword topic suggester
- LLM tagger among leaf topics
- Document page shows metadata + suggestions

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-21, AC-22 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
