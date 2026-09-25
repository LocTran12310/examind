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

`make verify f=.ai/features/2026092404-difficulty-at-upload` — **4/4** trên `local`, hai viewport, và từng ảnh đã
được đọc chứ không chỉ đếm assertion:

- **S1 ở 390px**: "Mức độ: Nhận biết · model gợi ý" — nửa đầu AC-06, mức và nguồn cùng một chỗ.
- **S2**: "Vận dụng cao" **không kèm nguồn** sau khi giáo viên đặt — nửa sau, mức của người thì không còn nói của ai.

**Không viết khối ô tick ở đây, và đây là lý do.** `evidence_check.py` đòi **mọi** acceptance criterion của feature
phải có ảnh ở mọi environment bắt buộc. Ba UoW kia không đổi một màn hình nào, nên AC-01…AC-05 không cách nào có
ảnh và công cụ báo đỏ đúng như thiết kế. Tick một ô mà chính công cụ ấy phản bác là kiểu nói dối nó sinh ra để chặn.

⚠ `scripts/gen_plan.py` dựng lại `uow.md` từ `plan_spec.py`, nên nó **xoá cả phần này lẫn mọi ô đã tick**. Chạy
`gen_plan` trước, tick sau.
