---
id: UOW-04
slug: review-ui
title: Thấy và sửa được mức độ ngay chỗ đang duyệt
demoable: true
duration: 2d
depends_on: []
requirements: [US-04]
verifies: [AC-06]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-04 — Thấy và sửa được mức độ ngay chỗ đang duyệt

## Demo script
1. Thẻ duyệt hiện mức độ và nói rõ máy gán hay người đặt, sửa ngay tại đó

## In scope
- difficulty on the review card
- provenance shown
- edit in place

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-06 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence
- [x] `make verify f=.ai/features/2026092404-difficulty-at-upload` green on local, the only required environment
- [x] Evidence exists for AC-06 at both viewports
- [x] `08-evidence.md` regenerated and its commit sha matches HEAD
- [x] Every screenshot read: S1 ở 390px hiện "Mức độ: Nhận biết · model gợi ý", S2 hiện "Vận dụng cao" không kèm
      nguồn sau khi giáo viên đặt — hai nửa của AC-06, đọc bằng mắt chứ không chỉ đếm assertion
