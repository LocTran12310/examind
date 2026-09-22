---
id: UOW-02
slug: switch-org
title: Active organisation in the token, header selector
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-03]
verifies: [AC-07, AC-08, AC-09, AC-10]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Active organisation in the token, header selector

## Demo script
1. Super admin opens the selector → all orgs → picks Trung tâm A → users/classes of A
2. Log out and in again → lands in Trung tâm A
3. Suspend Trung tâm A as super admin → selector no longer offers it; session falls back to system

## In scope
- Migration 0013 memberships
- deps scope from token + membership
- switch-org, /me/orgs
- OrgSwitcher wired

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-07, AC-08, AC-09, AC-10 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
