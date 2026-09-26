---
id: UOW-01
slug: exam-labels
title: Đề nói được nó thuộc môn nào, khối nào
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Đề nói được nó thuộc môn nào, khối nào

## Demo script
1. Tạo đề mới với môn Toán và khối 11: danh sách hiện 11 ở cột Lớp
2. Mở một đề cũ, chọn môn và khối, số được lưu ngay
3. Ma trận của đề chỉ mở chuyên đề của môn đã chọn

## In scope
- môn và khối ở form tạo đề
- sửa tại chỗ trên trang soạn đề

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03 pass
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
