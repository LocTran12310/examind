---
feature: 2026092405-blank-options
environments: [local]
viewports: [desktop, mobile]
---

# Verification — phương án là một số thì phải hiện ra số

Chạy trên ngân hàng thật. Câu dùng để kiểm là câu **"Khi cắt vật thể bởi mặt phẳng vuông góc với trục $Ox$…"**
(`ca023a77`), và nó được chọn vì bốn phương án của nó chia đúng hai nửa:

| Phương án | Nội dung | Trước bản sửa |
| --- | --- | --- |
| A | `$171\pi$.` | hiện bình thường — mở đầu bằng `$` nên Markdown không đọc thành danh sách |
| B | `171.` | **trống trơn** |
| C | `$18\pi$.` | hiện bình thường |
| D | `18.` | **trống trơn** |

Một câu, cả hai nhánh: thứ phải đổi và thứ phải không đổi nằm cạnh nhau trên cùng một khung hình, nên không thể
sửa được nửa này bằng cách làm hỏng nửa kia mà ảnh vẫn xanh.

**Mỗi bước có một khẳng định phân biệt được hai bản dựng.** `count … ol = 0` là cái đó: bản cũ render `171.`
thành `<ol start="171">` rỗng, nên con số này là **2** trên bản hỏng và **0** trên bản đã sửa. Một khẳng định chỉ
nói "có chữ 171" thì bản hỏng cũng thoả được nhờ chữ ở chỗ khác trên trang; một khẳng định chỉ nói "trang không
lỗi" thì thoả cả khi bốn ô trống rỗng — đúng kiểu ô xanh vô nghĩa mà `.ai/e2e/centre/screens` đã trả giá một lần.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Mở câu ấy từ ngân hàng: số hiện ra số, công thức vẫn là công thức, hình vẫn còn | `/org/bank` | `settle 4000; fill [aria-label="Tìm nội dung"] = cat vat the boi mat phang; settle 3500; click a:has-text("cắt vật thể"); settle 3500; scroll [data-testid=options]; settle 1000` | AC-01, AC-02 | `count [data-testid=options] ol = 0`; `count [data-testid=option-B]:has-text("171.") = 1`; `count [data-testid=option-A] .katex = 1`; `count [data-testid=question] img = 1`; `no-text=Có lỗi xảy ra` | local |
| S2 | Cả đề như học sinh đọc: không một phương án nào trong bài bị nuốt | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = Chuyên đề Hình học · 12A1; settle 3000; click button:has-text("Chuyên đề Hình học · 12A1"); settle 4500; scroll [data-testid=preview-q-1]; settle 1000` | AC-01 | `count [role=dialog] [data-testid^=option-] ol = 0`; `count [data-testid=preview-q-1] [data-testid=option-B]:has-text("171.") = 1`; `no-text=Có lỗi xảy ra` | local |

S2 quét **cả đề**, không riêng một câu: `[role=dialog] [data-testid^=option-] ol = 0` nói rằng không một phương án
nào trong bài — 15 câu — render thành danh sách. Đó là khẳng định gần nhất với điều anh thật sự cần ("học sinh
không thấy ô trống"), và nó là một con số, không phải một cảm nhận.

## Không kiểm ở đây

- **AC-03 (đề bài và lời giải giữ nguyên danh sách thật) không có ảnh, vì trong ngân hàng không có câu nào để
  chụp.** Tôi đã đếm: **0 câu** có đề bài, và **0 câu** có lời giải, chứa một danh sách đánh số thật (một dòng mở
  đầu bằng `1.` rồi có chữ). Soạn một câu như vậy chỉ để chụp một cái ảnh là thêm một câu bịa vào ngân hàng thật
  của anh — cái giá lớn hơn cái ảnh. Nó được chứng minh ở nơi dựng được trong ba dòng: `markdown.test.tsx` và
  `question-view.test.tsx`, gồm **một test đối chứng** khẳng định rằng **không** có chế độ cụm thì con số vẫn bị
  nuốt — tức là bộ test này đỏ trên bản dựng cũ, không phải luôn xanh.
- **Màn làm bài thật (một học sinh đang thi)** không có ảnh riêng. S2 chụp đúng thành phần ấy với `mode="review"`;
  còn `mode="exam"` — chế độ học sinh ngồi làm — được kiểm ở `question-view.test.tsx`. Lý do phải kiểm cả hai chế
  độ dù chỉ có một chỗ gọi: **chính vì chỉ có một chỗ gọi mà lỗi lan sang màn thi**, và một test ở một chế độ thì
  bản hỏng cũng thoả. Dựng một lượt thi thật cho đúng câu này đòi giao thêm một bài cho một lớp thật.

## Notes

Ô tìm kiếm của ngân hàng không cần dấu (`cat vat the boi mat phang`): cả nội dung lưu và câu tìm đều đi qua cùng
một bộ chuẩn hoá, nên bước này cũng là một lần kiểm cái lời hứa "không cần dấu" ở placeholder. Cụm ấy khớp đúng
**một** câu trong ngân hàng, và đề ở S2 khớp đúng **một** đề — kiểm bằng SQL trước khi viết bước, để `.first` của
runner không âm thầm bấm vào câu khác.
