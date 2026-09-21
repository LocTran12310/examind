---
id: UOW-01
slug: mastery
title: Mastery per topic follows every graded answer
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03, AC-08]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Mastery per topic follows every graded answer

## Demo script
1. A student submits an exam → 'Tiến độ của tôi' shows mastery per topic, weakest first
2. Teacher opens the class page → the student's weakest topics are listed
3. Run `python -m app.services.mastery backfill` → mastery rebuilt identically

## In scope
- Mastery table + update hook + backfill
- Mastery API
- Mastery in my stats and the class overview

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-08 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
