---
id: UOW-02
slug: roles
title: Vai trò lồng nhau: HS ⊂ GV ⊂ Admin
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06, AC-07]
risk: medium
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Vai trò lồng nhau: HS ⊂ GV ⊂ Admin

## Demo script
1. Đăng nhập giáo viên: thanh điều hướng có cả mục của học sinh
2. Giáo viên gọi endpoint phía học sinh của chính mình: 200, không phải 403

## In scope
- nav inheritance
- student endpoints accept staff

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-06, AC-07 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092402-exam-runner-and-roles` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
