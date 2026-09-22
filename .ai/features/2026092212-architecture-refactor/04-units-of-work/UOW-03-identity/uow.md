---
id: UOW-03
slug: identity
title: Identity: sessions, users, organisations
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-02, AC-04, AC-05, AC-06]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Identity: sessions, users, organisations

## Demo script
1. Đăng nhập, đổi mật khẩu, đổi tổ chức (không reload trang, cache xoá)
2. Người dùng: tạo, nhập CSV

## In scope
- auth
- me
- users + import
- orgs + admin
- membership

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-04, AC-05, AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4
