# Kịch bản end-to-end

Mỗi feature trong `.ai/features/` có `07-verification.md` của riêng nó, và mỗi bản chỉ chứng minh lát cắt của
feature đó. Thư mục này giữ thứ khác: một vòng đi hết chuỗi dạy học, cắt ngang nhiều feature, để bắt đúng loại
hỏng mà không bản nào kia bắt được — chỗ hai feature nối vào nhau.

Đây **không** phải một feature AI-DLC: không có code để gate, không có UoW, không bao giờ chặn G4. Các
environment của nó đều `required: false` một cách cố ý.

| | |
| --- | --- |
| `teaching-loop/` | duyệt câu hỏi → soạn đề theo ma trận → giao bài → bốn học sinh làm và nộp → giáo viên đọc báo cáo |

## Chạy

```bash
make e2e-fixture      # dựng lớp thử, 4 học sinh thử, chuyên đề thử, 10 câu hỏi (chạy lại được)
make e2e              # 20 bước, 6 phiên đăng nhập, ảnh chụp vào teaching-loop/evidence/
make e2e-teardown     # nói xem sẽ xoá gì
ARGS=--yes make e2e-teardown   # xoá nốt các bài làm (SQL) rồi dựng lại mastery
```

`make e2e` seed sẵn mã tổ chức vào cả sáu phiên trình duyệt; `.ai/credentials.env` phải có `E2E_TEACHER_*` và
`E2E_HS01..04_*` (script fixture in ra đúng những dòng đó).

## Nó chạy trên dữ liệu thật, và đây là điều phải biết trước

Vòng này chạy trên `trungtama` — tổ chức thật, màn hình thật, báo cáo thật. Nó **không** đụng tới học sinh hay
lớp có thật nào: fixture dựng lớp `E2E · lớp thử` và bốn tài khoản `e2e.hs01..04` của riêng nó.

| Thao tác | Trả lại được? |
| --- | --- |
| Duyệt một câu (S2) | **Có, và kịch bản tự làm** — S3 hoàn tác đúng lượt đó |
| Tạo đề, giao bài | Có — cho tới khi có học sinh làm |
| Bốn bài làm đã nộp | **Không, qua sản phẩm** — và điều đó là đúng: một câu trả lời thật không phải thứ giáo viên nên xoá được |

Nên mỗi vòng để lại một đề, một bài giao, bốn bài làm và 40 dòng `answer_facts`. `make e2e-teardown ARGS=--yes`
gỡ hết: nó in câu SQL xoá bài làm (các `answer_facts` đi theo vì khoá ngoại là `ON DELETE CASCADE`), chạy khi
được cho phép, rồi dựng lại mastery. Bốn tài khoản thử thì bị **vô hiệu hoá** chứ không xoá — sản phẩm không cho
gỡ một tài khoản khỏi tổ chức gốc của nó, và fixture bật lại chúng ở lần chạy sau.

**Dọn giữa hai lần chạy.** Chạy lại khi chưa dọn sẽ tạo đề thứ hai trùng tên và các bước sau bám vào đề đầu tiên
khớp bộ lọc.

## Một bài học đã trả giá

Bản đầu của script dọn hỏi `/assignments/search` bằng `{"exam_id": …}`. Endpoint đó **không có** bộ lọc ấy và bỏ
qua nó trong im lặng, nên câu hỏi "các bài giao của đề tôi" được trả lời bằng **mọi bài giao của tổ chức** — và
script suýt xoá bài giao thật của trung tâm. Thứ duy nhất chặn lại là API từ chối xoá một bài giao đã có người
làm.

Từ đó: **lọc bằng id mà chính script đã tự phân giải, không bằng một khoá đưa cho endpoint mà chưa kiểm là nó có
đọc hay không.** Một bộ lọc bị bỏ qua trông y hệt một bộ lọc không khớp gì, cho tới lúc nó khớp mọi thứ.
