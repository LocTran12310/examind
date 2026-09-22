---
id: UOW-03
slug: lists
title: All remaining lists on the DataTable
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-03, US-04]
verifies: [AC-08, AC-10, AC-11]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — All remaining lists on the DataTable

## Demo script
1. Documents, review, exams, assignments, AI models, tags: column filters + paging from the server
2. Exams: select a row → detail panel lists its questions
3. Bank: filters on the left + search, pages from the server, cards unchanged

## In scope
- Bare-list endpoints → Page
- List screens

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-08, AC-10, AC-11 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
