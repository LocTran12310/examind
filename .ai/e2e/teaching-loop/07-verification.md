---
feature: e2e-teaching-loop
environments: [e2e-teacher, e2e-hs01, e2e-hs02, e2e-hs03, e2e-hs04, e2e-report]
viewports: [desktop]
---

# Vòng dạy học — duyệt, soạn đề, giao bài, học sinh làm, báo cáo

Một vòng đi hết chuỗi, trên chính tổ chức thật `trungtama`, coi như bước tải đề lên đã xong. Mọi bản verification
khác trong repo chỉ chứng minh một lát cắt của một feature; bản này là thứ duy nhất chạy qua cả chuỗi, nên nó bắt
được đúng loại hỏng mà không bản nào kia bắt được: chỗ hai feature nối vào nhau.

**Chạy `python3 scripts/e2e_fixture.py` trước.** Nó dựng lớp `E2E · lớp thử`, bốn học sinh `e2e.hs01..04`,
chuyên đề `E2E · chuyên đề thử` và mười câu hỏi theo hình dạng đề THPT 2025 — bốn trắc nghiệm, ba đúng/sai bốn ý,
ba trả lời ngắn. Không một học sinh hay một lớp có thật nào bị đụng tới.

## Bốn học sinh, bốn bài làm khác nhau

Runner chạy **một bảng bước cho mọi environment**, nên nếu bốn em dùng chung một dòng bước thì bốn bài làm giống
hệt nhau và báo cáo không có phổ điểm nào để xem. Vì vậy mỗi em có dòng riêng, giới hạn bằng cột `Env`, với một
mẫu trả lời viết tay:

| Em | Trắc nghiệm | Đúng/Sai | Trả lời ngắn | Điểm | Cho thấy |
| --- | --- | --- | --- | --- | --- |
| hs01 | 4/4 | 3×4 ý đúng | 2/3 | **9.09** | đầu trên của phổ |
| hs02 | 4/4 | 3×3 ý đúng (0,5đ mỗi câu) | 3/3 | **7.27** | điểm thành phần của phần II |
| hs03 | 2/4 | 3+2+2 ý đúng | 1/3 | **3.64** | giữa phổ |
| hs04 | 1/4 | 3×1 ý đúng (0,1đ mỗi câu) | 0/3 | **1.0** | đáy phổ |

hs03 và hs04 cùng chọn **B** ở câu 3 và câu 4, nên "Hay chọn sai" có số thật chứ không phải một ô trống.

Điểm tính được vì đáp án biết trước: tổng thô 5,5 điểm (4×0,25 + 3×1 + 3×0,5) quy về thang 10. Mười câu dùng
**một khoá cho mỗi loại** — mọi câu trắc nghiệm đáp án A, mọi câu đúng/sai là Đ-Đ-S-Đ, mọi câu trả lời ngắn là 5.
Đó không phải sự lười: đề được sinh từ ma trận, và ma trận lấy câu ra khỏi chuyên đề theo thứ tự không ai hứa
hẹn, nên "câu ở vị trí 3" không phải cùng một câu giữa hai lần chạy. Một khoá cho mỗi loại làm đúng/sai độc lập
với thứ tự, và đó là điều kiện để bảng này nói được ai mấy điểm.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Hàng đợi duyệt liệt kê những đề còn phải xem | `/org/review` | `settle 3500` | AC-01 | `text=Duyệt câu hỏi`; `text=còn`; `no-text=Không tải được` | e2e-teacher |
| S2 | Duyệt một câu trong đề đầu tiên | `/org/review` | `settle 3500; click a[href^="/org/review/"]:not([href$="/untagged"]) >> nth=0; settle 3500; click button:has-text("Duyệt (Enter)"); settle 2500` | AC-01 | `text=còn`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | e2e-teacher |
| S3 | Trả lại nguyên trạng: hoàn tác lượt duyệt vừa rồi | `/org/bank` | `settle 3500; click button:has-text("Thay đổi gần đây"); settle 3000; click [data-testid=recent-changes] tr:has-text("Duyệt") button:has-text("Hoàn tác") >> nth=0; settle 3000` | AC-01 | `text=Đã hoàn tác 1 câu`; `no-text=Có lỗi xảy ra` | e2e-teacher |
| S4 | Tạo một đề mới | `/org/exams` | `settle 3000; click button:has-text("Tạo đề"); settle 1200; fill [role=dialog] input = E2E · vòng dạy học; click button:has-text("Tạo và soạn đề"); settle 4000` | AC-02 | `text=Ma trận đề`; `text=Câu hỏi trong đề` | e2e-teacher |
| S5 | Ma trận ba dòng theo chuẩn THPT, rồi sinh đề | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; fill [data-testid=row-0] [aria-label="Số câu"] = 4; click [data-testid=row-0] button >> nth=0; settle 1200; fill [aria-label="Tìm chuyên đề"] = E2E; settle 1200; click [role=treeitem]:has-text("E2E · chuyên đề thử"); settle 1200; click button:has-text("Thêm dòng"); settle 1000; click [data-testid=row-1] [aria-label="Loại câu"]; settle 800; click [role=option]:has-text("Đúng/Sai"); settle 600; fill [data-testid=row-1] [aria-label="Số câu"] = 3; click [data-testid=row-1] button >> nth=0; settle 1200; fill [aria-label="Tìm chuyên đề"] = E2E; settle 1200; click [role=treeitem]:has-text("E2E · chuyên đề thử"); settle 1200; click button:has-text("Thêm dòng"); settle 1000; click [data-testid=row-2] [aria-label="Loại câu"]; settle 800; click [role=option]:has-text("Trả lời ngắn"); settle 600; fill [data-testid=row-2] [aria-label="Số câu"] = 3; click [data-testid=row-2] button >> nth=0; settle 1200; fill [aria-label="Tìm chuyên đề"] = E2E; settle 1200; click [role=treeitem]:has-text("E2E · chuyên đề thử"); settle 1200; click button:has-text("Tạo đề theo ma trận"); settle 6000; scroll text=Câu hỏi trong đề; settle 1000` | AC-02 | `count [data-testid=exam-questions] = 1`; `no-text=Chưa có câu nào`; `no-text=blueprint-refusal` | e2e-teacher |
| S6 | Thang điểm của đề nói đủ ba phần | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; scroll text=Thang điểm của đề; settle 800` | AC-02 | `text=Thang điểm của đề`; `text=thang 10` | e2e-teacher |
| S7 | Giao cho lớp thử, tắt đảo câu và đảo phương án | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click button:has-text("Giao bài"); settle 1500; click label:has-text("E2E · lớp thử"); click label:has-text("Đảo thứ tự câu"); click label:has-text("Đảo phương án"); click [role=dialog] button:has-text("Giao bài"); settle 4000` | AC-03 | `count [data-testid=assigned] = 1`; `no-text=Có lỗi xảy ra` | e2e-teacher |
| S8 | hs01 nhận bài và làm gần như đúng hết | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 1"]; click [data-testid=option-A]; click [aria-label="Câu 2"]; click [data-testid=option-A]; click [aria-label="Câu 3"]; click [data-testid=option-A]; click [aria-label="Câu 4"]; click [data-testid=option-A]; click [aria-label="Câu 5"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Đúng"]; click [aria-label="Câu 6"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Đúng"]; click [aria-label="Câu 7"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Đúng"]; click [aria-label="Câu 8"]; fill [aria-label="Đáp án"] = 5; click [aria-label="Câu 9"]; fill [aria-label="Đáp án"] = 5; click [aria-label="Câu 10"]; fill [aria-label="Đáp án"] = 6; settle 4000` | AC-04 | `count [data-testid=timer] = 1`; `text=còn 0 câu chưa làm`; `text=Đã lưu` | e2e-hs01 |
| S9 | hs01 nộp bài và thấy điểm | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click button:has-text("Nộp bài"); settle 1500; click [role=dialog] button:has-text("Nộp bài"); settle 6000` | AC-04, AC-05 | `count [data-testid=score10] = 1`; `text=9.09` | e2e-hs01 |
| S10 | hs02 làm bài: trắc nghiệm đúng hết, phần đúng/sai sai một ý mỗi câu | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 1"]; click [data-testid=option-A]; click [aria-label="Câu 2"]; click [data-testid=option-A]; click [aria-label="Câu 3"]; click [data-testid=option-A]; click [aria-label="Câu 4"]; click [data-testid=option-A]; click [aria-label="Câu 5"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Sai"]; click [aria-label="Câu 6"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Sai"]; click [aria-label="Câu 7"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Sai"]; click [aria-label="Câu 8"]; fill [aria-label="Đáp án"] = 5; click [aria-label="Câu 9"]; fill [aria-label="Đáp án"] = 5; click [aria-label="Câu 10"]; fill [aria-label="Đáp án"] = 5; settle 4000` | AC-04 | `text=còn 0 câu chưa làm`; `text=Đã lưu` | e2e-hs02 |
| S11 | hs02 nộp bài | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click button:has-text("Nộp bài"); settle 1500; click [role=dialog] button:has-text("Nộp bài"); settle 6000` | AC-04, AC-05 | `count [data-testid=score10] = 1`; `text=7.27` | e2e-hs02 |
| S12 | hs03 làm bài ở mức trung bình | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 1"]; click [data-testid=option-A]; click [aria-label="Câu 2"]; click [data-testid=option-A]; click [aria-label="Câu 3"]; click [data-testid=option-B]; click [aria-label="Câu 4"]; click [data-testid=option-B]; click [aria-label="Câu 5"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Sai"]; click [aria-label="d Sai"]; click [aria-label="Câu 6"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Đúng"]; click [aria-label="d Sai"]; click [aria-label="Câu 7"]; click [aria-label="a Đúng"]; click [aria-label="b Đúng"]; click [aria-label="c Đúng"]; click [aria-label="d Sai"]; click [aria-label="Câu 8"]; fill [aria-label="Đáp án"] = 5; click [aria-label="Câu 9"]; fill [aria-label="Đáp án"] = 4; click [aria-label="Câu 10"]; fill [aria-label="Đáp án"] = 4; settle 4000` | AC-04 | `text=còn 0 câu chưa làm`; `text=Đã lưu` | e2e-hs03 |
| S13 | hs03 nộp bài | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click button:has-text("Nộp bài"); settle 1500; click [role=dialog] button:has-text("Nộp bài"); settle 6000` | AC-04, AC-05 | `count [data-testid=score10] = 1`; `text=3.64` | e2e-hs03 |
| S14 | hs04 làm bài yếu, sai giống hs03 ở câu 3 và câu 4 | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 1"]; click [data-testid=option-A]; click [aria-label="Câu 2"]; click [data-testid=option-B]; click [aria-label="Câu 3"]; click [data-testid=option-B]; click [aria-label="Câu 4"]; click [data-testid=option-B]; click [aria-label="Câu 5"]; click [aria-label="a Đúng"]; click [aria-label="b Sai"]; click [aria-label="c Đúng"]; click [aria-label="d Sai"]; click [aria-label="Câu 6"]; click [aria-label="a Đúng"]; click [aria-label="b Sai"]; click [aria-label="c Đúng"]; click [aria-label="d Sai"]; click [aria-label="Câu 7"]; click [aria-label="a Đúng"]; click [aria-label="b Sai"]; click [aria-label="c Đúng"]; click [aria-label="d Sai"]; click [aria-label="Câu 8"]; fill [aria-label="Đáp án"] = 4; click [aria-label="Câu 9"]; fill [aria-label="Đáp án"] = 4; click [aria-label="Câu 10"]; fill [aria-label="Đáp án"] = 4; settle 4000` | AC-04 | `text=còn 0 câu chưa làm`; `text=Đã lưu` | e2e-hs04 |
| S15 | hs04 nộp bài | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click button:has-text("Nộp bài"); settle 1500; click [role=dialog] button:has-text("Nộp bài"); settle 6000` | AC-04, AC-05 | `count [data-testid=score10] = 1`; `text=1` | e2e-hs04 |
| S16 | Báo cáo bài giao: đủ bốn bài, có điểm trung bình và phổ điểm | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=assigned] a >> nth=0; settle 4000` | AC-06 | `text=4/4`; `count [data-testid=average] = 1`; `count [data-testid=distribution] = 1` | e2e-report |
| S17 | Bốn học sinh, bốn điểm khác nhau | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=assigned] a >> nth=0; settle 4000; scroll [data-testid="st-e2e.hs04"]; settle 800` | AC-06 | `count [data-testid^="st-e2e"] = 4`; `text=9.09`; `text=7.27`; `text=3.64` | e2e-report |
| S18 | Theo câu hỏi: tỉ lệ đúng và phương án hay chọn sai | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click [data-testid=assigned] a >> nth=0; settle 4000; scroll text=Theo câu hỏi; settle 800` | AC-06 | `text=Theo câu hỏi`; `text=Hay chọn sai` | e2e-report |
| S19 | Hồ sơ một học sinh đã cộng bài vừa làm | `/org/users` | `settle 3500; fill [aria-label="Lọc Họ tên"] = E2E Học sinh 01; settle 2500; click a:has-text("E2E Học sinh 01"); settle 4000` | AC-07 | `text=Hồ sơ ·`; `text=bài`; `no-text=Học sinh chưa có lớp hoặc bài làm nào.` | e2e-report |
| S20 | Bản đồ nhiệt của lớp thử có số của cả bốn em | `/org/reports` | `settle 3500; click [role=tab]:has-text("Bản đồ nhiệt lớp"); settle 1500; click [aria-label="Lớp"]; settle 800; click [role=option]:has-text("E2E · lớp thử"); settle 4000` | AC-08 | `count [data-testid=heatmap] = 1`; `no-text=Chọn một lớp để xem bản đồ nhiệt.` | e2e-report |

## Không kiểm ở đây

- **Tổng quan theo khối.** Không phải chưa kiểm — **chưa tồn tại**. `answer_facts` không có cột khối
  (`app/shared/infrastructure/schema/assessment.py:132-156`), `ReportFilters` không có trục khối
  (`analytics/application/dto.py:17-27`), và `/org/reports` chỉ có hai trục Học kỳ và Lớp. Muốn có thì phải làm
  một feature, không phải thêm một bước vào bảng này.
- **Tự luận và đường chấm tay.** Chuẩn đề THPT 2025 không có phần tự luận, nên `"Cần chấm tự luận"` và
  `EssayGrader` nằm ngoài vòng này.
- **Hai chính sách xem kết quả còn lại** (`Sau khi đóng bài`, `Chỉ xem điểm`). Cả hai cần một bài giao đã đóng,
  tức thêm dữ liệu để lại trên tổ chức thật cho mỗi lần chạy. Chúng được kiểm ở `apps/api/tests`.
- **Tải đề lên và tách câu.** Theo yêu cầu, coi như đã xong. S1–S3 đi trên các đề thật đang còn câu chờ duyệt —
  hàng đợi duyệt bắt buộc phải có một `source_document` ở trạng thái `parsed`
  (`bank/infrastructure/read_models.py:318-327` bắt đầu từ chính bảng đó), nên không fixture nào thay được.

## Mỗi lần chạy để lại gì

Đây là phần phải đọc trước khi bấm chạy.

| Thao tác | Trả lại được? |
| --- | --- |
| Duyệt một câu (S2) | **Có, và kịch bản tự làm** — S3 hoàn tác đúng lượt đó, trả câu hỏi về trạng thái cũ |
| Tạo đề, giao bài (S4–S7) | Có — cho tới khi có học sinh làm |
| Bốn bài làm đã nộp (S8–S15) | **Không, qua sản phẩm** — `DeleteAssignmentHandler` từ chối xóa bài giao khi đã có bài làm |

Nên mỗi vòng để lại trên `trungtama`: một đề, một bài giao, bốn bài làm cùng `answer_facts` và phần mastery của
bốn tài khoản `e2e.hs*`. Tất cả đều mang tiền tố `E2E`/`e2e.`, không lẫn với dữ liệu của trung tâm, và
`scripts/e2e_teardown.py` gỡ sạch — kể cả câu SQL xóa bài làm, thứ nó chỉ in ra và đòi `--yes` chứ không tự chạy.

**Chạy lại mà chưa dọn thì S4 tạo thêm một đề trùng tên** và các bước sau sẽ bám vào đề đầu tiên khớp bộ lọc.
Dọn giữa hai lần chạy.

## Notes

Mỗi bước bắt đầu từ một lần tải trang mới — runner không kế thừa trạng thái của bước trước — nên S5 tới S7 và
S16 tới S18 đều phải tự đi lại từ `/org/exams` vào đúng cái đề của mình. Đó là lý do chúng dài, và là lý do
chúng dùng bộ lọc cột `"Lọc Đề"` thay vì "dòng đầu tiên": danh sách đề sắp theo thời gian tạo và trung tâm còn
những đề khác.

`"Nộp bài"` là nhãn của **cả** nút trên thanh **lẫn** nút xác nhận trong hộp thoại, nên cú nhấp thứ hai giới hạn
vào `[role=dialog]`; không thì nó chỉ mở lại hộp thoại vừa đóng. Cùng lý do, nút bắt đầu làm bài được chọn qua
`[data-testid="open-…"] button` chứ không qua nhãn: nhãn là `"Bắt đầu"` lần đầu và `"Làm tiếp"` khi có bài dở,
và một bước hỏng giữa chừng sẽ để lại đúng cảnh đó.

**S3 là thứ chứng minh S2.** Duyệt câu cuối cùng của một đề làm hàng đợi trống, duyệt câu giữa thì hiện câu
tiếp theo, nên không có một khẳng định nào đúng cho cả hai; S2 chỉ nói màn hình không lỗi. Bằng chứng thật nằm ở
S3: nếu S2 không duyệt được gì thì lịch sử không có dòng `"Duyệt"` nào mới để hoàn tác, và S3 đỏ. Đổi lại, khi
S2 hỏng vì lý do khác thì S3 sẽ hoàn tác **lượt duyệt gần nhất của tổ chức** — lượt đó cũng hoàn tác lại được từ
đúng màn hình ấy, nhưng hãy kiểm khi thấy vòng chạy đỏ.

Không bước nào assert số lần rời tab. Mỗi lần runner chụp ảnh là một lần tab xuống nền, và ứng dụng đếm đúng như
nó phải đếm — `"Rời tab n lần"` ở đây là tạo tác của phép đo, không phải hành vi của học sinh.

Ảnh của S5 dừng ở đầu trang chứ không ở danh sách câu, vì `Tạo đề theo ma trận` dựng lại cả trang và cuộn về
đầu. Nó vẫn cho thấy điều cần thấy: tiêu đề đọc `10 câu · tổng 5.5 điểm`, và thang điểm bên dưới nói Phần I 4
câu, Phần II 3 câu, Phần III 3 câu — tức ma trận đã chạy đúng ba dòng.

S15 chỉ assert `text=1` cho điểm của hs04 vì `1.0` được hiển thị là `1`; ba điểm kia là số lẻ nên nói được chính
xác. Bốn điểm khác nhau mới là điều đáng chứng minh, và S17 đọc lại cả ba trên cùng một màn hình.
