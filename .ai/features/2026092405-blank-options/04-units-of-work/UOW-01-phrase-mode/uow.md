---
id: UOW-01
slug: phrase-mode
title: Phương án được đọc như một cụm, không như một tài liệu
demoable: true
duration: 2d
depends_on: []
requirements: [US-01]
verifies: [AC-01, AC-02, AC-03]
risk: low
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Phương án được đọc như một cụm, không như một tài liệu

## Demo script
1. Câu có phương án 108. / 31. / 13. / 36. hiện đủ bốn số ở màn duyệt và màn làm bài
2. Phương án có công thức, chữ, hình không đổi
3. Đề bài có danh sách đánh số vẫn là danh sách

## In scope
- phrase mode in Markdown
- options use it

## Not in scope
- See other UoWs

## Risks
| Risk | Mitigation |
| --- | --- |
| None significant | — |

## Definition of done
- [x] All of AC-01, AC-02, AC-03 pass
- [x] Demo script executed end to end
- [x] Demoed and accepted at gate G4

## Verification evidence

`make verify f=.ai/features/2026092405-blank-options` — **4/4** trên `local`, hai viewport, ảnh đã đọc từng cái.

**AC-01 và AC-02 cùng một khung hình.** S1 cho thấy câu `ca023a77` với đủ bốn phương án: **A. 171π. · B. 171. ·
C. 18π. · D. 18.** — hai phương án B và D chính là hai ô trống trơn trước bản sửa, còn A và C chứng minh công
thức không bị chế độ cụm làm hỏng. Hình vẽ khối lăng trụ vẫn nằm đó. S2 cho thấy cùng câu ấy trong bản xem cả đề
"Chuyên đề Hình học · 12A1" (15 câu · 6.5 điểm), với khẳng định quét **cả đề**: không một phương án nào trong bài
render thành danh sách.

**Khẳng định phân biệt được hai bản dựng**, chứ không chỉ mô tả bản hiện tại: `count … ol = 0` đọc ra **2** trên
bản hỏng (B và D thành `<ol start="171">` và `<ol start="18">`) và **0** trên bản đã sửa. Đây là chỗ một bước kiểm
dễ thành ô xanh vô nghĩa nhất — "trang không có lỗi" đúng cả khi bốn ô trống rỗng.

**AC-03 không có ảnh, và không dựng được ảnh mà không bịa dữ liệu.** Trong ngân hàng thật: **0 câu** có đề bài và
**0 câu** có lời giải chứa danh sách đánh số thật. Nó được chứng minh ở `markdown.test.tsx` và
`question-view.test.tsx` — gồm một **test đối chứng** khẳng định rằng bỏ chế độ cụm thì con số vẫn bị nuốt, nên bộ
test này đỏ trên bản dựng cũ. Lý do đầy đủ nằm trong `07-verification.md › Không kiểm ở đây`.

**Màn làm bài (`mode="exam"`) được kiểm bằng test, không bằng ảnh** — và phải kiểm riêng dù chỉ có **một** chỗ gọi
`<Markdown phrase>`: chính vì chỉ có một chỗ gọi mà lỗi lan từ màn duyệt sang màn thi, nên một test ở một chế độ
thì bản hỏng cũng thoả.
