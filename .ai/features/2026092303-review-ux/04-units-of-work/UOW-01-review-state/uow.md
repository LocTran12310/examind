---
id: UOW-01
slug: review-state
title: One state per document, and every question reachable
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02]
verifies: [AC-01, AC-03, AC-04]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — One state per document, and every question reachable

## Demo script
1. POST /review/documents/search lọc review_state=pending → chỉ đề còn việc
2. POST /review/documents/{id}/questions/search state=approved → đọc lại câu đã duyệt

## In scope
- review_state + pending columns
- document questions by state
- re-decide through the existing command

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-03, AC-04 pass
- [x] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
