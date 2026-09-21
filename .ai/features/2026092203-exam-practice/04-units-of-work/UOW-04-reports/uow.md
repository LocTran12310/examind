---
id: UOW-04
slug: reports
title: Teachers and students see where marks were lost
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-05, US-06]
verifies: [AC-16, AC-17, AC-18, AC-19, AC-21]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Teachers and students see where marks were lost

## Demo script
1. Assignment report: submitted/not submitted, average, distribution, per-question % correct and most-chosen wrong option
2. 'Theo chuyên đề': tree with % correct at every level (Đại số 70% › Hàm số bậc hai 60% › …)
3. Group by tag / type / difficulty; filter by class
4. Class heatmap students × strands
5. Student 'Tiến độ của tôi': weakest topics first

## In scope
- Stats API (topics, groups, heatmap, assignment report)
- Report pages
- My stats page

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-16, AC-17, AC-18, AC-19, AC-21 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
