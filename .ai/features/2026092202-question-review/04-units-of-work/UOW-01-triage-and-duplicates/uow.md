---
id: UOW-01
slug: triage-and-duplicates
title: Parsed questions are triaged and de-duplicated automatically
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-05]
verifies: [AC-01, AC-02, AC-03, AC-07, AC-11, AC-13, AC-14, AC-20]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Parsed questions are triaged and de-duplicated automatically

## Demo script
1. Upload samples/exams/de-mau-toan10.docx and de-kho.docx
2. Open /org/review → each document shows Tự duyệt / Cần xem / Trùng counts and a progress bar
3. Upload de-mau-toan10.pdf (same questions) → its questions are marked Trùng and linked to the docx ones
4. As org_admin assign de-kho to a teacher → it appears under 'Của tôi' for that teacher

## In scope
- Migration (statuses, review_events, trgm)
- question_quality module
- Triage hook (search_text, dedupe, status, spot checks)
- Review documents API + assignment
- Review list UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03, AC-07, AC-11, AC-13, AC-14, AC-20 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
