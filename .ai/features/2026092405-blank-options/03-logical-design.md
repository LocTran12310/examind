---
feature: blank-options
adrs: 2
---

# Logical design

## Approach

`Markdown` dựng cả một tài liệu: tiêu đề, danh sách, trích dẫn, bảng. Với **đề bài** và **lời giải** thì đúng —
chúng là tài liệu. Với một **phương án** thì sai: phương án là một cụm, và mọi cấu trúc khối ở đó đều là hiểu
nhầm. `9.` không phải một danh sách bắt đầu từ 9; nó là số chín.

Nên `Markdown` nhận thêm một chế độ **cụm**: trước khi đưa chuỗi cho bộ render, thoát các ký tự mở đầu một cấu
trúc khối ở đầu mỗi dòng — dấu danh sách đánh số (`9.`, `9)`), dấu đầu dòng (`-`, `*`, `+`), tiêu đề (`#`), trích
dẫn (`>`). Chữ hiện ra không đổi một ký tự; chỉ cách bộ phân tích đọc nó đổi.

Chế độ ấy chỉ bật ở **nội dung phương án** (`QuestionView`), nơi duy nhất trong app render `o.content`. Đề bài,
lời giải, đáp án mẫu giữ nguyên đường cũ.

## Alternatives rejected

- **Sửa dữ liệu**: đổi `9.` thành `9\.` hoặc `$9$.` trong 104 phương án. Chữa triệu chứng — câu tiếp theo tải lên
  sẽ lại hỏng, và nó sửa thứ giáo viên đã soạn đúng.
- **Bỏ `remark-gfm`/danh sách khỏi toàn bộ Markdown.** Đề bài và lời giải có danh sách thật; tắt đi là hỏng chỗ
  khác để chữa chỗ này.
- **Bọc phương án trong `$…$`** để nó luôn là công thức. Phương án có khi là chữ, có khi là hình; ép tất cả thành
  công thức làm hỏng những cái đang đúng.
- **Chỉ thoát khi toàn bộ nội dung khớp `^\d+\.$`.** Vá đúng ảnh chụp này và để nguyên `9. và 10.` hay `- 5`.

## Error taxonomy

Không có mã lỗi. Đây là lỗi hiển thị, không có đường nào báo lỗi.

## ADRs

### ADR-01 — Phương án là một cụm, không phải một tài liệu
**Status:** accepted
Cấu trúc khối bị thoát trong nội dung phương án. Đây là ranh giới đúng: 1160 phương án trong ngân hàng, không
cái nào là một danh sách thật, trong khi 104 cái đang bị đọc nhầm thành danh sách. Đề bài và lời giải không đi
qua chế độ này vì ở đó danh sách là thật.

### ADR-02 — Sửa ở chỗ hiển thị, không sửa dữ liệu
**Status:** accepted
`9.` là nội dung đúng mà đề gốc có và giáo viên đã soạn. Sửa 104 dòng dữ liệu sẽ làm màn hình đúng hôm nay và
hỏng lại ở đề tải lên ngày mai. Chỗ hỏng là chỗ đọc, nên sửa ở chỗ đọc.
