---
id: UOW-07
slug: analytics-cleanup
title: Analytics, audit and removal of the old layout
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03, US-04]
verifies: [AC-01, AC-02, AC-04, AC-05, AC-06, AC-07, AC-08]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-07 — Analytics, audit and removal of the old layout

## Demo script
1. Báo cáo theo chuyên đề, thống kê cá nhân, luyện tập thích ứng
2. Cây thư mục cũ không còn; lint sạch

## In scope
- stats, mastery, adaptive, audit
- delete old folders
- architecture map
- final review

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-04, AC-05, AC-06, AC-07, AC-08 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
