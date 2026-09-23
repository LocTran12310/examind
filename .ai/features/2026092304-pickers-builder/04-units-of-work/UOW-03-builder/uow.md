---
id: UOW-03
slug: builder
title: A blueprint that reads well and a swap the teacher controls
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06, AC-07]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — A blueprint that reads well and a swap the teacher controls

## Demo script
1. Dòng ma trận nằm gọn một hàng ở màn rộng
2. Đổi câu: chọn từ ngân hàng hoặc để hệ thống chọn

## In scope
- blueprint row layout
- empty-topic message
- swap from the bank

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
- [x] `make verify f=.ai/features/2026092304-pickers-builder` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports (S1, S4, S5, S9, S10)
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
