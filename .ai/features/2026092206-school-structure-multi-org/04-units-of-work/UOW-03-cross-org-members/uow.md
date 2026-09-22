---
id: UOW-03
slug: cross-org-members
title: Accounts from other organisations
demoable: true
duration: 2d
depends_on: [UOW-02]
requirements: [US-04]
verifies: [AC-11, AC-12, AC-13]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Accounts from other organisations

## Demo script
1. Org admin of A: Người dùng → 'Thêm tài khoản có sẵn' → ttb / gvlan / Giáo viên → row with badge 'Từ ttb'
2. gvlan logs in with ttb → switches to A → sees A's classes; is teacher in A
3. Admin of A removes the membership → gvlan's next request in A is refused, account still works in ttb

## In scope
- link/unlink API
- Per-org role in user lists and checks
- Users page actions

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-11, AC-12, AC-13 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
