---
id: UOW-04
slug: admin-links
title: Đợt kiểm tra picker; org ↔ user assignment from both admin screens
demoable: true
duration: 2d
depends_on: [UOW-01]
requirements: [US-06]
verifies: [AC-12, AC-13, AC-14, AC-15, AC-16]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Đợt kiểm tra picker; org ↔ user assignment from both admin screens

## Demo script
1. Upload: Đợt kiểm tra 'Giữa kỳ 2' → document shows 'Giữa kỳ 2'; bank filter 'Giữa kỳ 2' finds its questions
2. Tổ chức → select Trung tâm B → members panel → add trungtama/buivanchau as student
3. Tài khoản → buivanchau → organisations panel lists Trung tâm A and Trung tâm B; remove B; history shows both changes

## In scope
- Exam period helper + pickers
- Membership service refactor + admin endpoints
- Members panel, Tài khoản page, orgs panel

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-12, AC-13, AC-14, AC-15, AC-16 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
