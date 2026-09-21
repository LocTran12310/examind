---
id: UOW-03
slug: results-and-grading
title: Students see feedback; teachers grade essays
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-04]
verifies: [AC-12, AC-13, AC-14]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Students see feedback; teachers grade essays

## Demo script
1. Student opens the result: each question shows their answer, the key and the solution; breakdown by section and topic
2. An 'after close' assignment shows only the total before closing
3. Teacher opens an attempt with an essay, gives 1.5/2 with a comment → student total updates and shows the comment

## In scope
- Result API with policies
- Essay grading API
- Result page
- Teacher attempt view with grading

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-12, AC-13, AC-14 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
