---
id: UOW-04
slug: flows
title: Every other screen on shadcn components, old barrel removed
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-01, US-04]
verifies: [AC-01, AC-12]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Every other screen on shadcn components, old barrel removed

## Demo script
1. Upload a document, review with hotkeys, edit a question, build and take an exam, see results and reports — in dark mode
2. `grep -r "@/components/ui\""` finds nothing; lint forbids it

## In scope
- Forms/dialogs/editors/runner/reports/topic tree
- Delete components/ui/index.tsx
- ESLint rule

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-12 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
