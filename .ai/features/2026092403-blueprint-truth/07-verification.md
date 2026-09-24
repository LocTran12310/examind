---
feature: 2026092403-blueprint-truth
environments: [e2e-teacher, e2e-hs01]
viewports: [desktop, mobile]
---

# Verification — Con số cạnh dòng ma trận là con số lệnh tạo đề sẽ dùng

**Chạy `python3 scripts/e2e_fixture.py --with-exam` trước** (lớp thử, bốn tài khoản `e2e.hs01..04`, đề đã giao —
cùng bộ dữ liệu mà `.ai/e2e/teaching-loop` dùng; `python3 scripts/e2e_teardown.py --yes` gỡ sạch).

Phép thử đi trên **dữ liệu thật của trung tâm**, vì chính nó là chỗ lỗi lộ ra: chuyên đề **"Mệnh đề"** có
**14 câu dùng được**, trong đó **7 câu Trắc nghiệm**, **7 câu Đúng/Sai**, **0 câu Trả lời ngắn** — tôi đếm bằng
chính phép lọc mà lệnh tạo đề dùng (`POST /questions/search` với `status: usable`). Không bước nào bấm "Tạo đề
theo ma trận", nên ma trận chỉ nằm trong state của trang và không một dòng nào được ghi.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Dòng Trắc nghiệm trên chuyên đề 14 câu đọc đúng 7 | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=row-0] button >> nth=0; settle 1200; fill [aria-label="Tìm chuyên đề"] = Mệnh đề; settle 1200; click [role=treeitem]:has-text("Mệnh đề"); settle 2500; scroll text=Ma trận đề; settle 800` | AC-01, AC-03 | `text=7 câu`; `text=14 câu dùng được`; `text=thiếu 3 câu`; `no-text=Có lỗi xảy ra` | e2e-teacher |
| S2 | Đổi loại câu thì số tính lại — Trả lời ngắn còn 0 | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=row-0] button >> nth=0; settle 1200; fill [aria-label="Tìm chuyên đề"] = Mệnh đề; settle 1200; click [role=treeitem]:has-text("Mệnh đề"); settle 2500; click [data-testid=row-0] [aria-label="Loại câu"]; settle 800; click [role=option]:has-text("Trả lời ngắn"); settle 2500; scroll text=Ma trận đề; settle 800` | AC-02 | `text=0 câu`; `text=chỉ 0 câu là`; `text=thiếu 10 câu`; `no-text=thiếu 3 câu` | e2e-teacher |
| S3 | Tình hình lớp không gọi chuyên đề nào là "yếu nhất" | `/org/classes` | `settle 3500; fill [aria-label="Lọc Lớp"] = E2E; settle 2500; click td:has-text("E2E · lớp thử"); settle 1500; click a:has-text("Mở trang lớp"); settle 4000; scroll text=Tình hình học tập; settle 800` | AC-04 | `text=Tình hình học tập`; `text=thấp trước`; `no-text=yếu nhất`; `no-text=Có lỗi xảy ra` | e2e-teacher |
| S4 | Nút chế độ xem có icon riêng cho từng chế độ | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000` | AC-05 | `count [role=radio][aria-label="Một câu"] svg = 1`; `count [role=radio][aria-label="Toàn đề"] svg = 1` | e2e-hs01 |

## Không kiểm ở đây

- **AC-04 ở màn kết quả bài làm và ở "Tiến độ của tôi".** Cả hai chỉ hiện mục theo chuyên đề khi người xem đã có
  bài làm, tức phải có một lượt nộp thật sinh `answer_facts` thật trên tổ chức của anh — cái giá quá đắt cho một
  dòng tiêu đề. Chúng được ghim ở `apps/web/src/__tests__/result.test.tsx` và `my-stats.test.tsx`, mỗi nơi vừa
  khẳng định chữ mới vừa khẳng định không còn chữ "yếu nhất".
- **Tooltip của nút chế độ xem.** Runner không có động tác trỏ chuột, nên không có cách nào làm tooltip hiện ra
  để chụp. S4 khẳng định phần chụp được — mỗi chế độ một icon và tên chế độ vẫn đọc được bằng trình đọc màn
  hình; phần chữ trong tooltip được ghim ở `exam-runner.test.tsx`.
- **Con số của dòng bằng đúng con số lệnh tạo đề lấy được.** Kiểm được điều này trong trình duyệt nghĩa là bấm
  tạo đề, tức ghi lại một đề. Nó được kiểm ở chỗ đúng hơn: cả hai đi qua cùng một phép lọc trong API, và tôi
  đã đối chiếu bằng tay trên dữ liệu thật — `POST /questions/search` với `status: usable` trả 14 / 7 / 7 / 0 cho
  "Mệnh đề" theo mọi loại / trắc nghiệm / đúng sai / trả lời ngắn.

## Notes

S1 và S2 đi qua cùng một đường tới đúng dòng ma trận ấy, vì runner nạp lại trang cho mỗi bước. Chuyên đề được
chọn bằng ô tìm trong hộp chọn chứ không bằng cách mở cây, để bước không phụ thuộc vào việc "Mệnh đề" nằm ở
nhánh nào.

S2 khẳng định `no-text=thiếu 3 câu`: con số cũ phải **biến mất** khi bộ lọc đổi, không chỉ có con số mới xuất
hiện. Một phép đếm không chịu tính lại sẽ vẫn xanh nếu chỉ khẳng định phần dương.

S2 khẳng định `text=chỉ 0 câu là` chứ không phải câu "chuyên đề chưa có câu hỏi nào dùng được": hai thông báo
khác nhau và sự khác nhau ấy chính là điều F21 thêm vào. Chuyên đề vẫn có 14 câu — thứ bằng 0 là **phần hợp bộ
lọc của dòng**, và bản thân việc màn hình phân biệt được hai chuyện đó là cái đáng chụp. Lần chạy đầu tôi khẳng
định nhầm sang câu kia, và nó đỏ trong khi tính năng đúng.

S3 khẳng định `no-text=yếu nhất` chứ không chỉ khẳng định chữ mới. Cái phải chứng minh là nhãn cũ **không còn ở
đó**, và một khẳng định dương một mình sẽ xanh cả khi hai dòng chữ cùng tồn tại.
