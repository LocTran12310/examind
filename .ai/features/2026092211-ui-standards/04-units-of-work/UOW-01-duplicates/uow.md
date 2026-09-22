---
id: UOW-01
slug: duplicates
title: Duplicate uploads: check, skip, re-parse, replace, keep both
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Duplicate uploads: check, skip, re-parse, replace, keep both

## Demo script
1. Upload a reference file again → 'Đã có file giống hệt' → Bỏ qua → nothing stored

## In scope
- check endpoint
- on_duplicate
- upload form choices
- golden runner re-parses

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
