---
id: UOW-01
slug: shell-theme
title: shadcn foundation, theme and app shell
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — shadcn foundation, theme and app shell

## Demo script
1. Sign in as trungtama/admin → left sidebar with icons, header right: org, theme, avatar menu
2. Toggle Tối → whole app dark, refresh keeps it; collapse sidebar to icons
3. Sign in as a student → same shell with student menu; phone width → menu opens as a sheet

## In scope
- shadcn init + components
- ThemeProvider
- AppSidebar, header, OrgSwitcher (current org), UserMenu
- Login / change-password pages

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
