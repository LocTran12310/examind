---
id: UOW-01
slug: dialogs-tables-spacing
title: Resizable dialogs, bordered zebra tables, compact spacing
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-05]
verifies: [AC-01, AC-02, AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Resizable dialogs, bordered zebra tables, compact spacing

## Demo script
1. Tags → Thêm tag → ⤢ Phóng to → Thu nhỏ → drag the right edge
2. Người dùng list: column borders, zebra rows
3. Phone width: page padding 8 px

## In scope
- FormDialog
- DataTable styles
- AppShell/PageHeader spacing

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
