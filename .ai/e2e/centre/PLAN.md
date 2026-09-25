# Kịch bản dữ liệu: một trung tâm như thật

Mục đích: có đủ dữ liệu để **mọi màn hình báo cáo** nói được điều gì — không phải "Chưa có dữ liệu" — và đặc biệt
là xem được **từng học sinh** và **từng lớp**, không chỉ con số tổng của trung tâm.

Khác `scripts/e2e_fixture.py` (4 học sinh, 1 lớp, 1 đề — để chạy kịch bản hồi quy) và `scripts/dev_rebuild.py`
(dựng tổ chức + upload đề). Cái này dựng phần còn lại: giáo viên, lớp, học sinh, đề, bài giao, và **bài làm thật
đã được chấm**.

## Điều quyết định hình dạng cả kịch bản, phải chốt trước

Bài làm sinh ra là **giả**. Điểm của một học sinh do script quyết định, không do em ấy làm bài. Điều đó vô hại với
mọi màn hình báo cáo — chúng chỉ cần dữ liệu có cấu trúc. Nhưng nó **phá huỷ đúng một thứ**: mục 4 của
`difficulty_report.py`, chỗ đối chiếu mức độ với tỉ lệ làm đúng thật. Đó là chỗ duy nhất nói được mức độ model gán
có **đúng** hay không, và hôm nay nó còn mẫu 0 câu.

Nếu bài làm giả được sinh ra *có* dùng mức độ làm đầu vào thì mục 4 sẽ tự xác nhận nhãn của chính nó — dữ liệu bịa
trông y như bằng chứng. Nếu sinh ra *không* dùng mức độ thì mục 4 sẽ báo "không có quan hệ" và trông như bằng
chứng rằng model vô dụng. **Cả hai đều là lời nói dối**, chỉ khác chiều.

Đã đề xuất chạy trên một tổ chức riêng để `trungtama` còn đo được thật về sau.

**Chủ dự án chốt: chạy ngay trên `trungtama`** (2026-09-25). Quyết định được ghi lại cùng cái giá của nó, vì cái
giá ấy không nhìn thấy được ở thời điểm trả nó:

> Từ lúc kịch bản này chạy, **mục 4 của `difficulty_report.py` trên `trungtama` không còn là bằng chứng về bất cứ
> điều gì.** Tỉ lệ làm đúng ở đó là tỉ lệ do script bốc ra, không phải do học sinh làm. Ai đọc con số ấy về sau —
> kể cả tôi ở một phiên khác — sẽ thấy một cột số đầy đặn trông hệt như dữ liệu thật.
>
> Muốn đo lại độ chính xác của mức độ thì phải xoá cơ sở dữ liệu và dựng lại (`dev_rebuild.py`), hoặc dựng một tổ
> chức thứ hai lúc ấy. Đây là điều dễ nhất để quên và đắt nhất khi quên.

Vì lý do đó, `scripts/seed_centre.py` **in cảnh báo ấy ra ngay trước khi ghi dòng đầu tiên** và đòi cờ `--yes`.
Một quyết định đã cân nhắc thì vẫn nên khó bấm nhầm lần thứ hai.

| | **chạy trên `trungtama`** (đã chọn) | chạy trên tổ chức riêng |
| --- | --- | --- |
| Thấy dashboard đầy dữ liệu | có | có |
| Còn đo được độ chính xác mức độ về sau | **không, cho tới khi xoá DB** | có |
| Giá | 0 | ~14 phút upload lại |

## Hình dạng trung tâm, và lý do của từng con số

Một trung tâm luyện thi THPT môn Toán. Không bịa nhiều hơn mức các ngưỡng đòi:

| | Số lượng | Vì sao đúng con số đó |
| --- | --- | --- |
| Giáo viên | 4 | Sản phẩm **không có** khái niệm giáo viên chủ nhiệm lớp (bảng `classes` không có cột nào trỏ tới giáo viên). "Nhiều giáo viên" chỉ có nghĩa là nhiều tài khoản cùng soạn đề và giao bài. 4 là đủ để thấy nhiều người cùng làm. |
| Lớp | 6 (`12A1`–`12A4`, `11A1`, `11A2`) | Hai khối để bộ lọc "Khối" và màn "Cơ cấu trường" có nội dung. Nội dung đề là Toán THPT nên khối 11–12 khớp, khối 10 thì không. |
| Học sinh | 150 (25 mỗi lớp) | Bản đồ nhiệt lớp là **học sinh × chuyên đề**; 25 dòng là một lớp thật. Phổ điểm của một bài giao cần ~20 bài nộp mới ra hình, nên 25 vừa đủ mà không phải bịa 200 em. |
| Đề | 36 | 6 lớp × 6 bài giao. Hai loại, xem dưới. |
| Bài giao | 36 | Mỗi lớp 6. |
| Bài làm đã nộp | ~900 | 150 em × 6. |
| Câu trả lời đã chấm | ~16 000 | Đây là thứ mọi báo cáo đọc (`answer_facts`). |

**Hai loại đề, và đây là chỗ dễ làm sai nhất.** Chia đều 22 câu của một đề thi thử ra khắp cây chuyên đề thì mỗi
cặp (học sinh, chuyên đề lá) chỉ được 2–3 câu — **dưới ngưỡng `MIN_ANSWERS = 5`** của
`analytics/domain/services/mastery.py:16`, nên "chuyên đề yếu nhất" của từng em sẽ rỗng và
`/classes/{id}/overview` in "chưa đủ dữ liệu". Cả màn hình quan trọng nhất với anh sẽ trắng.

Nên mỗi lớp có:
- **3 đề thi thử** — đúng hình dạng THPT 2025 (12 trắc nghiệm · 4 đúng/sai · 6 trả lời ngắn), rải khắp các mạch
  kiến thức. Việc của chúng là **bề rộng**: bản đồ nhiệt có ô ở mọi cột, báo cáo theo chuyên đề có mọi hàng.
- **3 đề chuyên đề** — 15 câu dồn vào **một** mạch kiến thức. Việc của chúng là **bề sâu**: mỗi em tích đủ ≥5 câu
  trên các chuyên đề lá của mạch ấy, nên mức nắm vững tụt được xuống dưới `WEAK_BELOW = 0.6` và "Cần ôn" hiện ra.
  Đây cũng là điều một trung tâm luyện thi làm thật: dạy hết một chuyên đề rồi kiểm tra chuyên đề đó.

Ba mạch được chọn để dồn khác nhau giữa các lớp, nên "chuyên đề yếu nhất" của lớp này khác lớp kia.

## Cách sinh đúng/sai, và giới hạn của nó

Mỗi học sinh có một **năng lực** θ và một **độ lệch theo mạch kiến thức**. Xác suất làm đúng một câu là
`clamp(θ + lệch_mạch + nhiễu)`. Không có số hạng nào theo **mức độ của câu hỏi** — đó là điều kiện để dữ liệu này
không tự xác nhận nhãn mức độ (xem phần đầu).

θ rải theo hình chuông lệch: vài em rất khá, phần lớn ở giữa, vài em yếu. Kết quả cần thấy được:
- **Phổ điểm** của một bài giao trải ra chứ không dồn một cột — `assignment_report.py:50-52` chia 10 cột cố định.
- **"Hay chọn sai"** có số: cần câu trắc nghiệm bị trả lời **sai** với `key_snapshot` — nên học sinh phải chọn một
  phương án cụ thể sai, không được để trống.
- **Bỏ trống thì không sinh gì.** Một câu không trả lời thì không có `answer_facts`, không có mastery
  (`assessment/application/common.py:170`). Nên học sinh trả lời **gần hết** các câu, sai thì sai chứ không bỏ.

Ba điều kịch bản này **không** thể làm cho có thật, nói rõ ngay:
- **Tỉ lệ làm đúng không đo được độ khó.** Xem phần đầu.
- **Độ phân biệt câu hỏi** (`discrimination`) sẽ là artefact của θ do script bốc, không phải của câu hỏi.
- **"Nghi sai đáp án"** (key audit) có thể nổ oan: nếu θ thấp làm 60% nhóm giỏi chọn cùng một phương án sai thì
  công cụ sẽ gắn cờ một câu có đáp án đúng. Không phải lỗi sản phẩm — là hệ quả của dữ liệu bịa.

## Thứ tự gọi, và bốn chỗ API sẽ cắn

1. Đăng nhập quản trị → đọc `/api/taxonomy`, `/api/topics`, `/api/grades/search`, `/api/school-years/search`.
   **Không tạo gì ở bước này**: tạo tổ chức đã seed sẵn môn, cấp học, khối, học kỳ, năm học đang hoạt động và cả
   cây chuyên đề Toán (`app/seed/org_template.py:13-56`).
2. 4 giáo viên: `POST /api/users {role:"teacher", password:"…"}` — **phải là quản trị mới tạo được giáo viên**;
   giáo viên chỉ tạo được học sinh (`accounts.py:20`).
3. 6 lớp: `POST /api/classes {name, grade_id}`.
4. 150 học sinh: `POST /api/users {role:"student", password:"…"}` — **truyền `password` tường minh**, vì chỉ khi đó
   `must_change_password` mới là False (`create_user.py:38-46`). Rồi một lần `POST /api/classes/{id}/members
   {user_ids:[…]}` cho mỗi lớp (không giới hạn số id).
   ⚠ **Không dùng `/api/users/import/commit`**: nó cố định `must_change_password=True`, học sinh không đăng nhập
   được (`import_users.py:70`).
5. 36 đề: `POST /api/exams` (đặt `settings.points_by_type` **ngay lúc tạo** — patch sau không đóng lại điểm của
   các câu đã thêm), rồi `POST /api/exams/{id}/blueprint {rows, seed, replace:true}`.
   ⚠ Một hàng ma trận trỏ vào chuyên đề **không có câu nào dùng được** thì **huỷ cả lệnh** với 422 `empty_topic`
   (`exam_rules.py:84`) — nên phải đọc số câu theo chuyên đề trước khi dựng ma trận, không đoán.
6. 36 bài giao: `POST /api/assignments {exam_id, class_ids, open_at, close_at, duration_minutes,
   shuffle_questions:false, shuffle_options:false}`.
   ⚠ Hai cờ `false` là điều kiện để script biết trước nhãn phương án. Mặc định chúng là **true**, và khi ấy nhãn
   A–D bị đánh lại theo từng lượt làm nên mọi đáp án tính trước đều sai.
   ⚠ `open_at` đặt trong quá khứ để bài mở ngay.
7. Mỗi học sinh: đăng nhập → `POST /api/assignments/{aid}/start` → `GET /api/attempts/{id}` (đọc đề **theo thứ tự
   của lượt làm ấy**) → một `PUT /api/attempts/{id}/answers/{qid}` cho từng câu → `POST …/submit`.
   ⚠ **Không có route lưu hàng loạt.** ~16 000 lệnh PUT, khoảng 7 phút.
   ⚠ **Giới hạn đăng nhập 30 lần/phút trên mỗi IP** (`config.py:28`) — 150 học sinh là 5 phút chỉ để đăng nhập.
   Cách gỡ: gửi `X-Forwarded-For` khác nhau cho từng em (máy dev tự tin cậy header ấy,
   `identity/interface/deps.py:154`), và **giữ cookie của từng em** để đăng nhập một lần rồi `refresh`, chứ không
   đăng nhập lại.
   ⚠ **Không cần worker**: chấm điểm, `answer_facts` và mức nắm vững được ghi **đồng bộ** trong chính request
   submit (`assessment/application/common.py:120-190`).
8. Phần đuôi, mỗi thứ nuôi một màn hình mà bảy bước trên không nuôi được:
   - **Ngày làm bài** phải nằm trong khoảng học kỳ, nếu không `term_code` là NULL và bộ lọc "Học kỳ" cùng các dòng
     HK1/HK2 trong hồ sơ học sinh rỗng (`calendar.py:36-42`). Hôm nay 25/09 nằm trong HK1 (05/09–15/01) nên "bây
     giờ" là hợp lệ — và nên để gần hiện tại, vì mức nắm vững có **chu kỳ bán rã 60 ngày** kéo mọi thứ về 0,5.
   - **Nhãn (tag)**: tab "Theo tag" cần `question_tags`. Gắn bằng `POST /api/questions/bulk {add_tag_ids}`.
   - **Đề ôn cá nhân**: `POST /api/classes/{id}/adaptive-assignments` cho 2 lớp.
   - **Lịch sử ôn tập** ở "Tiến độ của tôi": `POST /api/me/practice` cho ~30 em.
   - **"Cần chấm tự luận"**: đề THPT 2025 **không có phần tự luận**, nên phải tạo tay một câu essay
     (`POST /api/questions`) và một đề chứa nó, để nguyên không chấm.
9. `POST /api/analytics/mastery/rebuild` (quản trị) — không bắt buộc, dùng để **đối chiếu**: nó phát lại toàn bộ
   facts và phải ra đúng con số mà chấm trực tiếp đã ra. Lệch nhau là một lỗi thật.

## Kịch bản tự kiểm chứng ra sao

Không tin "chạy xong là xong". Sau khi chạy, script in một bảng và **mỗi dòng là một ngưỡng có thật trong code**:

| Kiểm | Ngưỡng | Nguồn |
| --- | --- | --- |
| Số cặp (học sinh, chuyên đề lá) có ≥5 câu | `MIN_ANSWERS = 5` | `mastery.py:16` |
| Số chuyên đề lá thực sự tụt dưới 0,6 ở ≥1 em | `WEAK_BELOW = 0.6` | `mastery.py:15` |
| Số câu hỏi đạt ≥10 lượt trả lời | `MIN_OBSERVATIONS = 10` | `bank/domain/services/item_stats.py:6` |
| Số bài giao có ≥20 bài nộp | hình phổ điểm | `assignment_report.py:50-52` |
| Số câu trắc nghiệm có ít nhất một lựa chọn sai | "Hay chọn sai" | `assignment_report.py` |
| `answer_facts` có `term_code` khác NULL | bộ lọc học kỳ | `calendar.py:36-42` |
| `answer_facts` có `class_ids` khác rỗng | mọi báo cáo theo lớp | `academic/…/repositories.py:106-111` |
| `answer_facts` có `topic_path` khác NULL | cây chuyên đề, bản đồ nhiệt | `bank/…/read_models.py:157-165` |

Rồi **mở từng màn hình bằng trình duyệt và đọc ảnh** — như F17/F18: assert xanh không có nghĩa ảnh cho thấy điều
nó khẳng định. Riêng bản đồ nhiệt và "chuyên đề yếu nhất" phải thực sự nhìn thấy nhiều màu và nhiều chuyên đề
khác nhau, không phải một cột đều tăm tắp.

## File sẽ đụng tới

| File | Việc |
| --- | --- |
| `scripts/seed_centre.py` | **mới** — toàn bộ kịch bản trên, qua HTTP, có `--dry-run` và bảng tự kiểm |
| `.ai/e2e/centre/PLAN.md` | **mới** — chính file này |
| `scripts/dev_rebuild.py` | thêm `--org` để dựng được tổ chức thứ hai |

## Ngoài phạm vi, nói rõ

- **Không dựng lại 34 học sinh và 6 lớp cũ của `trungtama`.** Chúng là dữ liệu thử của giai đoạn trước; kịch bản
  này thay thế chúng bằng một trung tâm có cấu trúc.
- **Không có giáo viên chủ nhiệm.** Sản phẩm chưa có khái niệm ấy; kịch bản không giả vờ là có.
- **`student_topic_week`** (ảnh chụp theo tuần) chỉ do worker ghi mỗi giờ và **không màn hình nào đọc** — bỏ.
