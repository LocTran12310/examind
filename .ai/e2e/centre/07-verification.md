---
feature: centre
environments: [local]
viewports: [desktop]
---

# Verification — các màn hình báo cáo nói được điều gì sau khi có dữ liệu thật

`scripts/seed_centre.py --yes` để lại 6 lớp · 150 học sinh · 36 bài giao · 900 bài nộp · 16 650 câu trả lời đã
chấm, và bảng tự kiểm của nó nói mọi ngưỡng đều vượt. Bản này tồn tại vì **bảng ấy không phải bằng chứng**: nó đọc
API, và một màn hình vẫn có thể trắng vì một lý do chẳng liên quan gì tới dữ liệu.

Chỉ một environment và một viewport: đây là kiểm chứng rằng **có dữ liệu để xem**, không phải kiểm chứng giao diện.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Báo cáo theo chuyên đề có hàng thật | `/org/reports` | `settle 4000; wait h1:has-text("Kết quả theo chuyên đề"); settle 2000` | data | `no-text=Chưa có dữ liệu làm bài`; `no-text=Có lỗi xảy ra` | local |
| S2 | Theo mức độ: cả bốn bậc đều có số | `/org/reports` | `settle 4000; click [role=tab]:has-text("Theo mức độ"); settle 2500` | data | `text=Nhận biết`; `text=Thông hiểu`; `text=Vận dụng`; `no-text=Chưa có dữ liệu` | local |
| S3 | Theo loại câu: ba loại của đề THPT | `/org/reports` | `settle 4000; click [role=tab]:has-text("Theo loại câu"); settle 2500` | data | `text=Trắc nghiệm`; `text=Đúng/Sai`; `text=Trả lời ngắn`; `no-text=Chưa có dữ liệu` | local |
| S4 | Bản đồ nhiệt của một lớp có ô màu | `/org/reports` | `settle 4000; click [role=tab]:has-text("Bản đồ nhiệt"); settle 1500; click [aria-label="Lớp"]; settle 800; click [role=option]:has-text("12A1"); settle 3000` | data | `no-text=Lớp chưa có học sinh`; `no-text=Chọn một lớp`; `count [data-testid=heatmap] = 1` | local |
| S5 | Danh sách lớp: cả sáu lớp, có sĩ số | `/org/classes` | `settle 4000; settle 1500` | data | `text=12A1`; `text=11A2`; `no-text=Chưa có lớp nào` | local |
| S6 | Một lớp: từng học sinh có chuyên đề cần ôn | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Mở trang lớp"); settle 4000; scroll h2:has-text("Tình hình học tập"); settle 1500` | data | `text=Tình hình học tập`; `count [data-testid^="ov-"] = 25` | local |
| S7 | Đề đã giao: danh sách bài giao có số đã nộp | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = Thi thử 12A1 lần 1; settle 2500; click td:has-text("Thi thử 12A1 lần 1"); settle 3000; click a:has-text("Soạn đề & giao bài"); settle 4000; scroll [data-testid=assigned]; settle 1500` | data | `text=đã nộp`; `no-text=Có lỗi xảy ra` | local |
| S8 | Một câu hỏi của ngân hàng mở được và hiện mức độ | `/org/bank` | `settle 4500; click [data-testid^="bank-"] a >> nth=0; settle 4000; settle 1500` | data | `count h1 = 1`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |
| S9 | Báo cáo bài giao: phổ điểm và từng học sinh | `/org/exams` | `settle 4000; fill [aria-label="Lọc Đề"] = Thi thử 12A1 lần 1; settle 2500; click td:has-text("Thi thử 12A1 lần 1"); settle 3000; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=assigned] a >> nth=0; settle 4000; settle 1500` | data | `text=Đã nộp`; `no-text=Có lỗi xảy ra` | local |
| S10 | Hồ sơ một học sinh theo năm học | `/org/classes` | `settle 4000; click td:has-text("12A1"); settle 2500; click a:has-text("Học sinh 001"); settle 4000; settle 1500` | data | `text=Hồ sơ`; `no-text=Có lỗi xảy ra` | local |
| S11 | Theo tag: nhãn nguồn từ 18 đề có số | `/org/reports` | `settle 4000; click [role=tab]:has-text("Theo tag"); settle 2500` | data | `no-text=Chưa có dữ liệu`; `no-text=Có lỗi xảy ra` | local |
| S12 | Cơ cấu trường: hai khối, sáu lớp, 150 học sinh | `/org/structure` | `settle 4000; settle 1500` | data | `text=THPT`; `no-text=Chưa có lớp`; `no-text=Có lỗi xảy ra` | local |

## Không kiểm ở đây

- **Con số có đúng hay không.** Bài làm là bịa; những bước trên chỉ chứng minh màn hình **có gì để hiện** và không
  rơi vào nhánh rỗng. Một phổ điểm đẹp ở đây không nói gì về học sinh thật.
- **Độ khó của câu hỏi.** Xem cảnh báo đầu `PLAN.md`: tỉ lệ làm đúng trên tổ chức này không còn đo được điều gì.
- **S6 không khẳng định mọi học sinh đều có chuyên đề yếu.** 144 trong 150 em có; sáu em còn lại chưa đủ 5 câu
  trên bất kỳ chuyên đề lá nào, và dòng "chưa đủ dữ liệu" của họ là màn hình **nói đúng**, không phải lỗi. Bước
  này khẳng định đủ 25 dòng học sinh; các badge chuyên đề yếu thì **đọc bằng mắt** trên ảnh.
- **S8 không khẳng định câu ấy đủ lượt trả lời.** 289 trong 396 câu đủ 10 lượt, nhưng câu đứng đầu danh sách là
  câu nào thì phụ thuộc thứ tự mặc định — ép nó phải là một trong 289 câu kia chỉ tạo ra một bước đỏ vì lý do
  chẳng liên quan. Con số 289/396 đã được đếm thẳng trên `answer_facts`, là chỗ đếm được; bước này chỉ chứng minh
  trang chi tiết mở được trên dữ liệu vừa seed.

## Notes

Các bước khẳng định bằng `no-text=` trên đúng những câu mà màn hình in khi rỗng (`TopicStatsTree` in "Chưa có dữ
liệu làm bài.", `Heatmap` in "Lớp chưa có học sinh.", `ClassOverview` in "chưa đủ dữ liệu"). Khẳng định phủ định là
cách đúng ở đây: điều cần chứng minh là **không rơi vào nhánh rỗng**, và một khẳng định dương trên một con số cụ
thể sẽ vỡ mỗi lần seed chạy lại với `--seed` khác.

S6 `scroll` trước khi khẳng định vì "Tình hình học tập" nằm dưới màn: một khẳng định xanh vẫn cho ra tấm ảnh không
thấy thứ nó nói (bài học đã ghi trong `AGENTS.md`).
