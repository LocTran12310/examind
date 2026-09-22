---
id: UOW-01
slug: facets-tags
title: Tags by subject, subject 'none' / school-year filters, facet counts API
demoable: true
duration: 2d
depends_on: []
requirements: [US-02, US-03, US-04]
verifies: [AC-03, AC-05, AC-06, AC-07, AC-09]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Tags by subject, subject 'none' / school-year filters, facet counts API

## Demo script
1. GET /questions/facets?subject_id=<Toán> → topics with subtree counts, types, periods, tags
2. Create a Toán tag → /tags?subject_id=<Lý> does not list it; source tags listed for both
3. school_year=2024-2025 keeps only questions from 2024-2025 files

## In scope
- Migration 0016 + backfill
- bank filters
- facets endpoint
- tags API subject

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-03, AC-05, AC-06, AC-07, AC-09 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
