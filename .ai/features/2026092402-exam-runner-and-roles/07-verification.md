---
feature: 2026092402-exam-runner-and-roles
environments: [e2e-hs01, e2e-teacher]
viewports: [desktop, mobile]
---

# Verification — Khung làm bài đứng yên, xem được cả đề, và giáo viên thử được đề mình giao

Hai vai trên cùng một stack: một học sinh làm bài, một giáo viên kiểm đề và xem thanh điều hướng của mình.
Runner lặp environment ở vòng ngoài, và đây cũng là thứ tự đọc của bảng dưới.

**Chạy `python3 scripts/e2e_fixture.py --with-exam` trước.** Nó dựng lớp thử, bốn tài khoản `e2e.hs01..04`, mười
câu hỏi theo hình dạng đề THPT 2025, và giao sẵn đề `E2E · vòng dạy học` cho lớp đó — bốn trắc nghiệm, ba đúng/sai,
ba trả lời ngắn, tắt đảo câu và đảo phương án. Không một học sinh hay lớp có thật nào bị đụng tới. Đây là cùng bộ
dữ liệu mà `.ai/e2e/teaching-loop` dùng, và `python3 scripts/e2e_teardown.py --yes` gỡ sạch.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Khung làm bài ở một câu trắc nghiệm | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 1"]; settle 1200` | AC-01 | `count [data-testid=exam-question] = 1`; `count .mx-auto.w-full.max-w-5xl = 1`; `text=Phần I` | e2e-hs01 |
| S2 | Cùng khung ấy ở một câu trả lời ngắn — nội dung ngắn hơn hẳn | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [aria-label="Câu 10"]; settle 1200` | AC-01 | `count [data-testid=exam-question] = 1`; `count .mx-auto.w-full.max-w-5xl = 1`; `text=Phần III` | e2e-hs01 |
| S3 | Bật "Toàn đề": cả mười câu cùng hiện | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [role=radio]:has-text("Toàn đề"); settle 2000` | AC-02 | `text=Phần I`; `text=Phần II`; `text=Phần III`; `no-text=Câu sau` | e2e-hs01 |
| S4 | Trả lời ngay trên trang toàn đề | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [role=radio]:has-text("Toàn đề"); settle 2000; click [data-testid=option-A] >> nth=0; settle 2500; scroll [aria-label="Câu 1"]; settle 800` | AC-03 | `no-text=còn 10 câu chưa làm`; `no-text=Có lỗi xảy ra` | e2e-hs01 |
| S5 | Quay lại "Một câu" thì về đúng câu vừa làm | `/home` | `settle 3000; click [data-testid="open-E2E · vòng dạy học"] button; settle 5000; click [role=radio]:has-text("Toàn đề"); settle 2000; click [role=radio]:has-text("Một câu"); settle 1500` | AC-02 | `count [data-testid=exam-question] = 1`; `text=Câu sau` | e2e-hs01 |
| S6 | Thanh điều hướng của giáo viên có cả mục của học sinh | `/org/review` | `settle 3500; click [aria-label="Mở menu"]; settle 1500` | AC-06 | `count a[href="/home"] = 1`; `count a[href="/me/stats"] = 1`; `count a[href="/org/bank"] = 1` | e2e-teacher |
| S7 | "Tiến độ của tôi" mở được, và không mời giáo viên tạo đề ôn | `/me/stats` | `settle 3500; wait h1:has-text("Tiến độ của tôi"); settle 1500` | AC-07 | `count h1:has-text("Tiến độ của tôi") = 1`; `no-text=Tạo đề ôn tập`; `no-text=Có lỗi xảy ra` | e2e-teacher |
| S8 | "Bài được giao" của giáo viên trả lời được, không 403 | `/home` | `settle 3500; wait text=Đang mở; settle 1500` | AC-07 | `text=Đang mở`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | e2e-teacher |
| S9 | Vào được bản chạy thử từ danh sách Đã giao | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click a:has-text("Làm thử"); settle 4000` | AC-04 | `text=Chạy thử`; `text=không ghi lại gì`; `count [data-testid=exam-question] = 1` | e2e-teacher |
| S10 | Chạy thử được chấm ngay, và nói rõ không ghi gì | `/org/exams` | `settle 3000; fill [aria-label="Lọc Đề"] = E2E · vòng; settle 2500; click td:has-text("E2E · vòng dạy học"); settle 1500; click a:has-text("Soạn đề & giao bài"); settle 4000; click a:has-text("Làm thử"); settle 4000; click [data-testid=option-A]; settle 1500; click button:has-text("Chấm thử"); settle 1500; click [role=dialog] button:has-text("Chấm thử"); settle 4000` | AC-05 | `count [data-testid=score10] = 1`; `text=không ghi lại gì` | e2e-teacher |

## Không kiểm ở đây

- **AC-05, phần "không ghi một dòng nào".** Một trình duyệt không đếm được bảng. Nó được chứng minh ở nơi đếm
  được: `apps/api/tests/test_assignments_api.py::test_a_trial_run_is_scored_and_writes_nothing` cho một học sinh
  thật làm và nộp trước — để các con số khác 0 và có thứ để làm hỏng — rồi đếm `Attempt`, `AttemptAnswer`,
  `AnswerFact`, `TopicMastery` và đọc lại toàn bộ JSON của báo cáo bài giao quanh lần chạy thử; cả bốn con số và
  cả bản báo cáo giống hệt. Bản unit còn khẳng định `FakeUow.commits == 0`.
- **AC-01, phép đo bề rộng.** Một bước không so được hai lần chụp với nhau. Nó khẳng định cặp lớp chính là bản vá
  (`.mx-auto.w-full.max-w-5xl`), còn việc khung đứng yên thì **đọc bằng mắt**: S1 ở một câu trắc nghiệm bốn phương
  án và S2 ở một câu trả lời ngắn — hai loại nội dung lệch nhau nhất trong đề — và hai tấm ảnh phải cho thấy cùng
  một khung.
- **Học sinh nộp bài.** Không bước nào nộp: nộp sinh `answer_facts` thật trên tổ chức thật, và F20 không có gì cần
  chứng minh ở đó. Một lượt làm dở sẽ bị worker quét và không để lại fact nào.

## Bằng chứng này không gác cổng, và đây là lý do

`evidence_check.py` đòi **mọi** acceptance criterion phải có ảnh ở **mọi** environment được đánh dấu bắt buộc.
Tính năng này trải trên hai vai, nên điều đó không thể đúng: "giáo viên thấy mục của học sinh" không kiểm được
khi đang là học sinh, và "chế độ toàn đề lưu được câu trả lời" không kiểm được khi đang là giáo viên. Tôi đã thử
bật cờ ấy lên cho `e2e-teacher` và `e2e-hs01`: công cụ lập tức đòi AC-05, AC-06 và AC-07 ở `e2e-hs01`, thứ không
cách nào dựng ra được.

Nên hai environment ấy để `required: false`, và bằng chứng ở đây **được ghi và được đọc** chứ không được máy ép.
Cái chốt còn lại là lời khẳng định rằng chúng đã được đọc thật — 20/20 ảnh, từng tấm một.

## Notes

`no-text=Câu sau` ở S3 là cách nói "đây không còn là chế độ một câu": nút chuyển câu chỉ tồn tại ở chế độ ấy. Ngược
lại S5 khẳng định nó quay lại.

S4 khẳng định bằng `no-text=còn 10 câu chưa làm` chứ không phải `text=còn 9 câu chưa làm`: điều đáng chứng minh là
một cú nhấp trên trang toàn đề **có được ghi nhận**, và một khẳng định phủ định không vỡ nếu một lần chạy trước đó
để lại một câu đã trả lời.

S6 bấm nút menu rồi khẳng định trên **DOM** chứ không trên chữ, vì đúng một nút ấy làm hai việc trái ngược theo
bề rộng: ở 390px nó mở thanh bên ra, ở 1440px nó thu thanh bên lại thành dải biểu tượng. Một khẳng định trên nhãn
sẽ xanh ở màn này và đỏ ở màn kia vì lý do chẳng liên quan gì tới tính năng. `a[href="/home"]` và `a[href="/me/stats"]` có mặt cạnh `a[href="/org/bank"]` trên trang của một giáo viên **là**
điều AC-06 nói, và nó đúng dù thanh ấy đang mở, đang thu, hay đang là một sheet. Khẳng định không bám vào
`aria-label` của thanh bên: bản sheet ở 390px không mang nhãn ấy, và một lần chạy đã đỏ vì đúng lý do đó trong
khi ảnh chụp cho thấy nhóm "Học tập" nằm ngay đó.

Hệ quả của cú bấm ấy: ở 1440px ảnh của S6 cho thấy một dải biểu tượng đã thu, nên tấm **đọc được** cho AC-06 là
tấm ở 390px — nơi sheet mở ra và nhóm "Học tập › Bài được giao · Tiến độ của tôi" nằm ngay dưới các mục của giáo
viên. Tấm desktop góp phần đếm DOM. Hai tấm cùng nhau mới là bằng chứng đầy đủ, và nói ra điều đó đúng hơn là
giả vờ rằng một trong hai đủ.

S7 chờ và khẳng định trên `h1` chứ không trên chữ trần. "Tiến độ của tôi" là **hai** thứ trên màn hình: tiêu đề
trang và nhãn của chính mục ấy trong thanh điều hướng. Sau khi S6 thu thanh bên lại, nhãn kia còn trong DOM nhưng
đã ẩn — và `text=` bắt phần tử **đầu tiên**, tức cái đang ẩn, rồi đợi nó hiện ra suốt ba mươi giây. Một khẳng
định đỏ vì trỏ nhầm phần tử là thứ tốn thời gian nhất để đọc, vì nó trông y hệt một lỗi thật.

S7 và S8 chờ chữ đầu tiên xuất hiện thay vì chỉ đợi một khoảng cố định. Hai trang đó là hai route mà lần chạy
trước chưa ai mở, nên lần đầu chúng còn phải biên dịch — một lần chạy sau khi dựng lại container thấy trang trắng
trong hơn mười giây, rồi trang hiện ra đúng lúc ảnh được chụp. Ảnh khi ấy cho thấy điều mà khẳng định vừa bảo là
không có, và đó là kiểu bằng chứng tệ nhất: nó trông như một lỗi thật.

S7 khẳng định `no-text=Tạo đề ôn tập`. Đây là chỗ quy tắc vai trò lồng nhau **dừng lại**, và nó đáng được một
khẳng định riêng: một lượt ôn tập tạo ra lượt làm bài thật cùng `answer_facts` thật, nên bài ôn của giáo viên sẽ
nằm trong số liệu của trung tâm như thể một học sinh đã làm.

Các bước của học sinh đều bắt đầu lại từ `/home` vì runner nạp lại trang cho mỗi bước; nút vào bài được chọn qua
`[data-testid="open-…"] button` chứ không qua nhãn, vì nhãn là "Bắt đầu" lần đầu và "Làm tiếp" khi đã có bài dở —
và từ S2 trở đi thì luôn là trường hợp thứ hai.
