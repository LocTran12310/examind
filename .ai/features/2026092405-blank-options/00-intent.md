---
feature: blank-options
slug: 2026092405-blank-options
owner: Loc Tran
created: 2026-09-24
status: approved
---

# Intent — Phương án là một số thì đang biến mất

## Problem
Loc Tran, khi duyệt một câu (chat, 2026-09-24, kèm ảnh): *"Câu này bị gì? đáp án chưa hiển thị đúng"* — phương án
A và D trống trơn trên bản xem trước, trong khi ô soạn thảo ghi rõ `9.` và `5.`.

Nguyên nhân dựng lại được: **`9.` là cú pháp danh sách đánh số của Markdown**. Bộ render biến nó thành
`<ol start="9">` rỗng — số bị ăn làm dấu đầu dòng, dấu chấm bị ăn làm dấu phân cách, và không còn chữ nào để
hiện. Phương án B và C sống sót chỉ vì chúng bắt đầu bằng `$` (công thức), không phải chữ số.

Đo trên ngân hàng thật: **104 phương án thuộc 34 câu** đang bị nuốt như vậy — 9% số phương án. Có câu trống cả
bốn lựa chọn (`108.` / `31.` / `13.` / `36.`).

Và đây không dừng ở màn duyệt: phương án được render bằng **cùng một component** ở màn làm bài. **Một học sinh
đang thi những câu đó sẽ thấy bốn ô trống.**

## Affected personas
| Persona | Current behaviour | Desired behaviour |
| --- | --- | --- |
| Học sinh làm bài | Thấy phương án trống, không có gì để chọn | Thấy đúng con số đã soạn |
| Giáo viên duyệt | Tưởng câu hỏi hỏng, không biết vì sao | Thấy đúng nội dung, không phải đoán |

## Success signal
34 câu ấy hiện đủ phương án ở cả màn duyệt lẫn màn làm bài, không phải sửa một dòng dữ liệu nào.

## Out of scope
- Đổi nội dung câu hỏi trong cơ sở dữ liệu — lỗi nằm ở chỗ hiển thị, không nằm ở dữ liệu
- Đổi cách render **đề bài** và **lời giải**: ở đó một danh sách đánh số là thứ hợp lệ và có thật

## Constraints
| Kind | Detail |
| --- | --- |
| Data | Không migration, không sửa dữ liệu |
| Scope | Chỉ những chỗ nội dung là một **cụm**, không phải một tài liệu |
