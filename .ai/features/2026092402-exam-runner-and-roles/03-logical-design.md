---
feature: exam-runner-and-roles
adrs: 4
---

# Logical design

## Approach

Bốn việc, ba trong số đó nhỏ hơn vẻ ngoài của chúng.

**Bề rộng.** `Runner` là `mx-auto max-w-5xl` và cha của nó là `<main class="flex flex-col">`. Trên một flex item,
`margin-inline: auto` **huỷ `align-items: stretch`**, nên khung co về đúng bề rộng nội dung — và nội dung đổi theo
từng câu. Thêm `w-full` là xong: `max-w-5xl` vẫn chặn trên, `w-full` giữ đáy. Cùng lỗi ấy phải soát lại ở mọi chỗ
khác dùng đúng cặp `mx-auto max-w-*` bên trong một flex column.

**Toàn đề.** Chế độ thứ hai của cùng một `useExamRunner`: thay vì render `questions[index]`, render cả danh sách,
mỗi câu vẫn là `QuestionView` + `AnswerInput` cũ, vẫn gọi đúng `change()` đang có. Không đụng vào tự lưu, đồng hồ,
bảng câu hay nộp bài. Chế độ nằm trong state của trang, không lên URL: nó là sở thích lúc làm bài, không phải một
địa chỉ để chia sẻ.

**Chạy thử.** Không mượn đường của attempt (ADR-01): hai endpoint không ghi gì.
- `GET /assignments/{id}/paper` — đề đúng như học sinh thấy: thứ tự câu của đề, `answer`/`is_true`/`solution` bị
  tước, không đồng hồ, không hạn nộp.
- `POST /assignments/{id}/trial` `{responses}` — chấm trong bộ nhớ bằng đúng `scoring.grade` và trả về đúng hình
  dạng `GET /attempts/{id}/result`.
Cả hai là `staff_actor`. Không một dòng nào được ghi, nên không có gì để loại khỏi báo cáo về sau.

**Vai trò lồng nhau.** Một hàm ở `lib/common/nav.ts` mở rộng vai trò thành tập vai trò nó bao hàm
(`student ⊂ teacher ⊂ org_admin`), và phía API các handler phía học sinh đổi `actor.role != "student"` thành "có
phải người dùng của tổ chức này không". Quan trọng: điều này **không** cho giáo viên xem dữ liệu của học sinh ở
những màn đó — `my_assignments` vẫn lọc theo `actor.user_id`, nên giáo viên thấy bài của chính mình.

## Alternatives rejected

- **Cho giáo viên một attempt thật có cờ `trial`.** Mỗi chỗ tổng hợp — báo cáo bài giao, mastery, heatmap, hồ sơ
  học sinh, snapshot tuần — đều phải nhớ lọc nó ra, và quên một chỗ là sai số liệu mà không ai thấy. Cách rẻ hơn
  và chắc hơn là không ghi gì cả.
- **Chấm ở phía client.** Bản xem của học sinh đã tước đáp án, và phải giữ như vậy: gửi đáp án xuống trình duyệt
  để chấm nghĩa là ai mở tab mạng cũng đọc được.
- **Bỏ chế độ một câu.** Trên điện thoại, một câu một màn là cách đọc đúng; "toàn đề" là thêm một lựa chọn chứ
  không thay thế.
- **Đưa chế độ xem lên URL.** Một địa chỉ chia sẻ được ngụ ý rằng nó đáng chia sẻ; đây là sở thích cá nhân lúc
  làm bài.

## Error taxonomy

| Code | HTTP | When |
| --- | --- | --- |
| `not_found` | 404 | Bài giao không thuộc tổ chức của người gọi |
| — | 403 | Người gọi không phải nhân viên (chạy thử là việc của người ra đề) |

## ADRs

### ADR-01 — Chạy thử không ghi gì
**Status:** accepted
Không attempt, không `answer_facts`, không mastery, không sự kiện. Đây là điều kiện để câu trả lời "báo cáo lớp có
đổi không?" luôn là "không", mà không cần ai nhớ một bộ lọc nào. Cái giá là giáo viên không xem lại được lần chạy
thử của mình sau khi rời trang — chấp nhận được: nó là bản kiểm đề, không phải một lượt thi.

### ADR-02 — Vai trò là tập lồng nhau, khai báo một chỗ
**Status:** accepted
`student ⊂ teacher ⊂ org_admin`, viết một lần trong `nav.ts` và dùng lại. Danh sách `roles` của từng mục điều
hướng giữ nguyên ý nghĩa "vai trò thấp nhất thấy được mục này", nên thêm một mục mới không phải nhớ liệt kê cả ba.

### ADR-03 — Chế độ xem nằm trong state, không lên URL
**Status:** accepted
Xem `Alternatives rejected`. Hệ quả: tải lại trang thì quay về chế độ một câu, và đó là mặc định đúng.

### ADR-04 — Đề của bản chạy thử đi qua cùng một hàm tước dữ liệu với attempt
**Status:** accepted
Nếu viết một hàm thứ hai để dựng "đề cho giáo viên xem", hai hàm sẽ lệch nhau, và ngày chúng lệch là ngày đáp án
rò ra một trong hai đường. Dùng lại đúng hàm mà `GET /attempts/{id}` đang dùng.
