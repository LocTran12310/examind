# Bằng chứng kiểm chứng — trung tâm đã seed (2026-09-25)

Bốn vòng chạy trình duyệt trên cùng một bộ dữ liệu: 6 lớp · 150 học sinh · 36 đề · 900 bài nộp ·
16 850 câu trả lời đã chấm. **32/32 bước xanh**, và mỗi ảnh đã được đọc chứ không chỉ được đếm.

| Vòng | Phủ gì | Kết quả | Chạy lại |
| --- | --- | --- | --- |
| [`.ai/e2e/centre`](e2e/centre/07-verification.md) | Báo cáo (5 tab), lớp, bản đồ nhiệt, báo cáo bài giao, ngân hàng, cơ cấu trường, hồ sơ học sinh | **12/12** | `make verify f=.ai/e2e/centre` |
| [`.ai/e2e/centre/screens`](e2e/centre/screens/07-verification.md) | Mọi mục còn lại của quản trị: đề đã tải lên, chưa gắn chuyên đề, năm học, người dùng, chuyên đề, tags, model AI, cấu hình tách đề | **10/10** | `make verify f=.ai/e2e/centre/screens` |
| [`.ai/e2e/centre/student`](e2e/centre/student/07-verification.md) | Phía `hs001`: bài được giao, tiến độ, **làm thật một đề ôn cá nhân rồi nộp** | **6/6** | `make verify f=.ai/e2e/centre/student` |
| [`.ai/features/2026092404-difficulty-at-upload`](features/2026092404-difficulty-at-upload/07-verification.md) | Thẻ duyệt: mức độ kèm nguồn, sửa tại chỗ | **4/4** | `make verify f=.ai/features/2026092404-difficulty-at-upload` |

Ảnh nằm ở `<thư mục>/evidence/<env>/<viewport>/<Sn>.png`, kèm một tấm ghép `contact-sheet-<env>.png` mỗi
environment. `08-evidence.md` do `--write` sinh ra và ghi commit sha của lúc chạy.

## Cách một bước được coi là xanh

Không phải "có ảnh". Một bước xanh khi trang đạt trạng thái sẵn sàng, không tín hiệu lỗi nào nổ, không
`console.error` nào, **và mọi khẳng định trong cột `Assert` đều đúng**. Cột ấy là thứ tách "trang tải được" khỏi
"con số đúng"; thiếu nó thì cả vòng xanh trên một tính năng tính sai vẫn xanh.

Các vòng này khẳng định theo lối **phủ định** — `no-text=Chưa có dữ liệu`, `no-text=Lớp chưa có học sinh` — bám
đúng câu mà mỗi màn hình in khi rỗng. Cố ý không ghim một con số: số đổi theo `--seed`, còn thứ cần chứng minh là
màn hình **không rơi vào nhánh rỗng**.

## Ba điều bốn vòng này KHÔNG chứng minh

1. **Con số có đúng không.** Mọi bài làm do `scripts/seed_centre.py` sinh ra. Cấu trúc là thật — ai yếu chuyên đề
   nào so với bạn cùng lớp, phổ điểm có trải không — còn tỉ lệ đúng thì không.
2. **Độ khó câu hỏi.** Tỉ lệ đúng ở đây được sinh từ năng lực học sinh, **không** từ mức độ, nên "Theo mức độ"
   phẳng 60–66% là artefact chứ không phải phát hiện. Mục 4 của `difficulty_report.py` trên tổ chức này đã hỏng
   vĩnh viễn — xem [`e2e/centre/PLAN.md`](e2e/centre/PLAN.md).
3. **Thời gian làm bài.** Luôn 0 giây, vì server kẹp `seconds_spent` vào thời gian thực sự trôi qua và script trả
   lời cả bài trong chưa tới một giây. Màn hình đang nói thật về dữ liệu bịa.

## Một bước của chính tôi đã xanh mà nói dối

`screens/S10` bấm `td:has-text("hs001")` — không đi đâu cả — rồi khẳng định `no-text=Có lỗi xảy ra`, thứ đúng
luôn trên chính trang danh sách đang đứng. Bước báo xanh trong khi ảnh chụp trang Người dùng chứ không phải hồ sơ.
**Runner không bắt được; đọc ảnh mới bắt được.** Đã sửa để khẳng định `text=Hồ sơ`.

Đó là lý do "đọc từng ảnh" không phải nghi thức: một khẳng định quá yếu để phân biệt trang định mở với trang đang
đứng sẽ xanh mãi mãi.

## Các vòng trước, trên dữ liệu riêng của chúng

`.ai/e2e/teaching-loop` (20/20, sáu phiên, bốn học sinh làm bài thật) và bảy feature có `08-evidence.md` riêng —
F14, F15, F16, F18, F20, F21, F22. Chúng chạy trước lần dựng lại cơ sở dữ liệu hôm nay, nên ảnh của chúng nói về
dữ liệu khi ấy; `08-evidence.md` của mỗi vòng ghi commit sha tương ứng.
