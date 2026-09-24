---
id: UOW-02
slug: no-labels
title: Bỏ nhãn xếp hạng, và nút chế độ xem có icon
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-04, AC-05]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-02 — Bỏ nhãn xếp hạng, và nút chế độ xem có icon

## Demo script
1. Ba màn theo chuyên đề: thứ tự giữ nguyên, không còn chữ yếu nhất
2. Nút Một câu / Toàn đề có icon và tooltip

## In scope
- remove ranking labels
- mode toggle icons

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-04, AC-05 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092403-blueprint-truth` green on local, the only required environment
- [x] Evidence exists for every AC in `verifies`, at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: each one shows the claim its step makes, on the page the step names
