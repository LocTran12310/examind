---
id: UOW-03
slug: key-audit
title: Suspect answer keys are flagged for review
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-04]
verifies: [AC-09, AC-10, AC-11, AC-12]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Suspect answer keys are flagged for review

## Demo script
1. Seed: flip the key of a question answered by ≥ 10 students → run 'Kiểm tra đáp án' → it appears as 'Nghi sai đáp án' with evidence
2. In the queue press the right option key, then Enter → approved and usable again
3. A hard but correct question is not flagged

## In scope
- Detection service + worker schedule + exclusion
- Flagged group in review UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-09, AC-10, AC-11, AC-12 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
