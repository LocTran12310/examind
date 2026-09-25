---
feature: 2026092501-class-overview-and-subjects
environments: [local]
viewports: [desktop, mobile]
---

# Verification — cả lớp, lịch sử làm bài, và báo cáo khi có nhiều môn

Chạy trên trung tâm đã seed: 6 lớp · 150 học sinh · 36 bài giao · 900 bài nộp.

**Ba chỗ bước kiểm cố tình không khẳng định một con số cụ thể**: điểm trung bình, số lượt và phần trăm đều đổi
mỗi lần seed chạy lại với `--seed` khác. Thứ cần chứng minh là màn hình **có gì để hiện** và **không rơi vào
nhánh rỗng** — nên các khẳng định bám vào nhãn và vào câu mà mỗi màn hình in khi rỗng.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Trang lớp mở ra ở Tổng quan, với số của cả lớp | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500` | AC-03 | `count [data-testid=cs-assignments] = 1`; `count [data-testid=cs-average] = 1`; `count [data-testid=cs-distribution] = 1`; `text=Chuyên đề lớp còn yếu` | local |
| S2 | Rê vào một cột phổ điểm: khoảng điểm, số bài, phần trăm | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; hover [data-testid=bucket-6]; settle 1500` | AC-03 | `text=điểm`; `text=bài đã nộp`; `no-text=Có lỗi xảy ra` | local |
| S3 | Tab Học sinh vẫn là danh sách như cũ | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4500; click [role=tab]:has-text("Học sinh"); settle 2500` | AC-03 | `count [data-testid=cs-average] = 0`; `no-text=Có lỗi xảy ra` | local |
| S4 | Hồ sơ học sinh có lịch sử làm bài với cột thời gian | `/org/users` | `settle 4000; fill [aria-label="Lọc Tên đăng nhập"] = hs001; settle 2500; click a:has-text("Học sinh 001"); settle 4500; scroll text=Lịch sử làm bài; settle 1500` | AC-01 | `count [data-testid=attempt-history] = 1`; `text=Lịch sử làm bài`; `text=Thời gian`; `no-text=Em này chưa làm bài nào` | local |
| S5 | Báo cáo mặc định vẫn là mọi môn | `/org/reports` | `settle 4500; settle 1500` | AC-05 | `count [aria-label="Môn"] = 1`; `text=Mọi môn`; `no-text=Chưa có dữ liệu làm bài` | local |

## Không kiểm ở đây

- **Cột "Thời gian" sẽ hiện 0 phút** trên mọi lượt của dữ liệu seed, và đó là **đúng** (A-03): script trả lời cả
  bài trong chưa tới một giây, nên `submitted_at − started_at` thật sự bằng 0. Bước S4 vì vậy khẳng định cột ấy
  **có mặt**, không khẳng định giá trị của nó. Con số ấy chỉ có nghĩa khi học sinh thật làm bài.
- **Nhóm theo môn ở báo cáo (AC-06)** không kiểm được ở đây: trung tâm này dạy đúng một môn, và với một môn thì
  màn hình **cố tình** nhìn y như cũ — không tiêu đề môn nào. Dựng môn thứ hai chỉ để chụp một tiêu đề là thêm
  một môn giả vào ngân hàng thật. Nó được chứng minh ở nơi dựng được hai môn trong ba dòng:
  `reports.test.tsx`, ba test — mặc định không gửi `subject_id`, hai môn thì nhóm, một môn thì không.
- **Thứ tự menu (AC-07).** Có một bước cho nó và tôi đã bỏ, vì nó không kiểm được điều nó nói. Bảng khẳng định
  chỉ có `count`, `text=` và `no-text=` — không có cách nào nói "cái này đứng trước cái kia" — nên bước ấy chỉ
  khẳng định **ba link tồn tại**, thứ đúng cả trước lẫn sau khi đổi thứ tự. Một khẳng định không phân biệt được
  hai trạng thái thì không phải bằng chứng, nó chỉ là một ô xanh.

  Nó còn đỏ ở 390px vì thanh bên thu thành sheet nên link chưa có trong DOM — đúng cái bẫy `AGENTS.md` đã ghi
  ("khẳng định trên nhãn thanh bên xanh ở desktop và đỏ ở mobile vì lý do chẳng liên quan tới tính năng"), và
  tôi vẫn đâm vào. Thứ tự được ghim ở `nav.test.ts`, nơi so được cả mảng một lúc.

## Notes

S1–S3 đều đi lại từ `/org/classes` vì runner nạp lại trang cho mỗi bước. Bấm hàng lớp mở **bảng chi tiết bên
dưới**, không sang trang — trang lớp nằm sau nút "Mở trang lớp". Bài học ấy đã trả giá một lượt đỏ ở
`.ai/e2e/centre`.

S4 lọc theo `hs001` rồi bấm **tên học sinh**: chỉ tên mới là link. Bấm vào ô tên đăng nhập chỉ chọn hàng — và
một bước như thế từng **xanh mà nói dối** ở `.ai/e2e/centre/screens`, vì khẳng định `no-text=Có lỗi` đúng luôn
trên trang danh sách đang đứng.
