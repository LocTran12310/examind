---
id: UOW-03
slug: class-fill
title: Rót một lớp mới từ một lớp cũ trong một lần bấm
demoable: true
duration: 2d
depends_on: []
requirements: [US-03]
verifies: [AC-08, AC-09, AC-10, AC-11]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-03 — Rót một lớp mới từ một lớp cũ trong một lần bấm

## Demo script
1. Hộp Thêm học sinh có hai đường: tìm từng em, và từ một lớp cũ
2. Chọn một lớp cũ: cả danh sách hiện ra, tích sẵn, thêm một lần
3. Em đã ở trong lớp đích được đánh dấu và không tích được

## In scope
- chọn lớp nguồn
- danh sách có tích sẵn
- một lần gọi add_members

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-08, AC-09, AC-10, AC-11 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify` — **10/10**, ảnh đã đọc. S5 cho thấy lớp **12A99 · 2027-2028** (lớp trống của năm mới), hộp thoại
mở ở tab "Từ lớp cũ", lớp nguồn **11A1 · 2026-2027**, **25 ô tích sẵn**, một nút **"Thêm 25 học sinh"**, và
dòng chỉ sang "Năm học › Chuyển năm học".

**Danh sách lớp bám theo năm ở thanh trên**, nên bước phải đổi năm trước khi tìm lớp — bản đầu thiếu chỗ ấy và
đỏ với "không tìm thấy 12A99" trong khi lớp vẫn nằm nguyên trong cơ sở dữ liệu.

**Bước dừng ngay trước nút "Thêm"**: con số 25 đã nói cả lớp nguồn được đọc **và** mọi em được tích sẵn, còn
bấm thật sẽ ghi 25 dòng vào một lớp thật mà lấy lại phải xoá từng em qua hai trang bảng. Một lời gọi duy nhất
cho cả lớp chốt ở `classes.test.tsx`, nơi đếm được số lần gọi `POST /classes/{id}/members`. **AC-09 và AC-10**
cũng ở đó: cả hai cần một lớp nguồn có em đã nằm sẵn trong lớp đích, dựng được trong ba dòng và không ghi vào
dữ liệu thật.
