---
feature: centre-screens
environments: [local]
viewports: [desktop]
---

# Mọi màn hình còn lại, trên dữ liệu của trung tâm đã seed

`.ai/e2e/centre` đã đi qua các màn hình báo cáo, `.ai/e2e/centre/student` đi qua phía học sinh, và
`.ai/features/2026092404-difficulty-at-upload` đi qua thẻ duyệt. Bản này phủ nốt **mọi mục còn lại trong thanh
điều hướng của quản trị trung tâm**, lấy đúng danh sách từ `apps/web/src/lib/common/nav.ts` chứ không đoán.

**Mỗi bước mở một màn hình bằng URL và khẳng định ba điều**: trang dựng được (`h1` tồn tại), không rơi vào nhánh
lỗi, và không rơi vào nhánh rỗng. Cố ý không khẳng định trên một con số cụ thể — số sẽ đổi mỗi lần seed chạy lại
với `--seed` khác, còn thứ cần chứng minh là **màn hình có gì để hiện trên dữ liệu này**.

Đi bằng URL chứ không bấm qua thanh bên: hôm nay đã mất bốn lượt chạy đỏ vì đoán selector, và một bước điều hướng
hỏng thì không nói được gì về màn hình nó định mở.

## Steps

| ID | Step | Path | Interaction | Verifies | Assert | Env |
|---|---|---|---|---|---|---|
| S1 | Đề đã tải lên: 18 đề, trạng thái đã tách | `/org/documents` | `settle 4500; settle 1500` | data | `count h1 = 1`; `no-text=Chưa có đề nào`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |
| S2 | Chưa gắn chuyên đề | `/org/review/untagged` | `settle 4500; settle 1500` | data | `count h1 = 1`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |
| S3 | Năm học: năm đang hoạt động và hai học kỳ | `/org/school-years` | `settle 4500; settle 1500` | data | `count h1 = 1`; `text=2026-2027`; `no-text=Có lỗi xảy ra` | local |
| S4 | Cơ cấu trường: hai khối, sáu lớp | `/org/structure` | `settle 4500; settle 1500` | data | `count h1 = 1`; `text=THPT`; `no-text=Có lỗi xảy ra` | local |
| S5 | Người dùng: 4 giáo viên và 150 học sinh | `/org/users` | `settle 4500; settle 1500` | data | `count h1 = 1`; `text=hs001`; `no-text=Có lỗi xảy ra` | local |
| S6 | Chuyên đề: cây Toán đã seed | `/org/topics` | `settle 4500; settle 1500` | data | `count h1 = 1`; `no-text=Chưa có chuyên đề`; `no-text=Có lỗi xảy ra` | local |
| S7 | Tags: nhãn nguồn của 18 đề | `/org/tags` | `settle 4500; settle 1500` | data | `count h1 = 1`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |
| S8 | Model AI: model phân loại đang bật | `/org/ai-models` | `settle 4500; settle 1500` | data | `count h1 = 1`; `text=qwen2.5:7b`; `no-text=Có lỗi xảy ra` | local |
| S9 | Cấu hình tách đề | `/org/settings/ingestion` | `settle 4500; settle 1500` | data | `count h1 = 1`; `no-text=Có lỗi xảy ra`; `no-text=Không tải được` | local |
| S10 | Hồ sơ một học sinh theo năm học và học kỳ | `/org/users` | `settle 4500; fill [aria-label="Lọc Tên đăng nhập"] = hs001; settle 2500; click a:has-text("Học sinh 001"); settle 4000` | data | `text=Hồ sơ`; `text=Năm học`; `no-text=Có lỗi xảy ra` | local |

## Không kiểm ở đây

- **Con số có đúng không.** Bài làm là bịa (`.ai/e2e/centre/PLAN.md`); các bước chỉ chứng minh màn hình dựng được
  và có dữ liệu để hiện.
- **Màn hình của super admin** (`/admin/orgs`, `/admin/users`). Tài khoản chạy bản này là quản trị **trung tâm**,
  và hai mục ấy chỉ hiện với super admin — dựng một phiên super admin chỉ để mở hai danh sách là thêm một đường
  đăng nhập nữa phải giữ, đổi lấy rất ít.
- **Các luồng ghi** — tạo đề theo ma trận, giao bài, sửa hàng loạt rồi hoàn tác. Chúng có bản kiểm riêng ở
  `.ai/features/2026092304-pickers-builder`, `2026092305-bulk-safety` và `2026092403-blueprint-truth`, chạy trên
  dữ liệu dựng riêng cho chúng. Lặp lại ở đây chỉ thêm rác vào trung tâm mà không thêm bằng chứng.

## Notes

`no-text=` bám vào đúng câu mỗi màn hình in khi rỗng, nên một bước xanh nghĩa là **không rơi vào nhánh rỗng** —
mạnh hơn `count h1 = 1` đứng một mình, vốn cũng xanh trên một trang trắng có tiêu đề.

S10 lọc theo `hs001` (duy nhất) rồi bấm **tên học sinh** — chỉ tên mới là link; bấm vào ô tên đăng nhập chỉ chọn
hàng.

**Bản đầu của bước này xanh mà nói dối.** Nó bấm `td:has-text("hs001")`, không đi đâu cả, và hai khẳng định
`no-text=Có lỗi xảy ra` / `no-text=Không tải được` đúng luôn trên chính trang danh sách — nên bước báo xanh trong
khi ảnh cho thấy trang Người dùng chứ không phải hồ sơ. Runner không bắt được; **đọc ảnh mới bắt được**. Giờ nó
khẳng định `text=Hồ sơ`, thứ chỉ trang hồ sơ mới có.
