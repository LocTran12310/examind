---
id: UOW-02
slug: org-management
title: Super admin manages organisations
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-04]
verifies: [AC-10, AC-11, AC-12, AC-13, AC-14]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Super admin manages organisations

## Demo script
1. Log in as super admin, open /admin/orgs
2. Create org `TrungtamA` with admin `admin` → temporary password shown once
3. Try to create `TRUNGTAMA` → field error
4. Log in as trungtama/admin in a private window → forced password change → org admin home
5. Suspend TrungtamA → that login is refused with 'Tổ chức đang bị khóa'; reactivate → allowed
6. Soft delete a test org → hidden from list; system org shows no suspend/delete

## In scope
- Taxonomy + topic + tag schema and per-org seed from the Toán template
- Org service and /admin/orgs API
- Admin orgs UI

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-10, AC-11, AC-12, AC-13, AC-14 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
