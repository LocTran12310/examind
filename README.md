# Examind

Ngân hàng câu hỏi, đề ôn luyện và đề ôn tập cá nhân hoá cho trung tâm, giáo viên và học sinh.
Chạy self-host bằng Docker Compose: Postgres (ltree + pgvector), MinIO, FastAPI, Next.js, Caddy,
một worker xử lý tài liệu, Ollama tuỳ chọn.

Tải lên đề Word/PDF của trường hoặc Sở, hệ thống đọc công thức MathType thành LaTeX, tách từng câu
kèm đáp án và lời giải, gắn chuyên đề, rồi từ ngân hàng đó tạo đề theo ma trận, giao bài cho lớp,
chấm tự động và báo cáo theo chuyên đề.

## Chạy nhanh

```bash
cp .env.example .env          # đổi JWT_SECRET, mật khẩu admin, APP_ENCRYPTION_KEY trước khi mở ra ngoài
make up                       # build và chạy cả stack
open http://localhost:8088/login
```

Tài khoản đầu tiên là tài khoản hệ thống: tổ chức `system`, tên đăng nhập và mật khẩu lấy từ
`SUPERADMIN_USERNAME` / `SUPERADMIN_PASSWORD` trong `.env` (lần đầu bắt buộc đổi mật khẩu).
Từ đó tạo tổ chức, giáo viên và lớp.

## Lệnh thường dùng

```bash
make            # liệt kê mọi lệnh
make dev        # chỉ Postgres (:55442) và MinIO (:59100) để chạy api/web ở máy
make api-dev    # uvicorn --reload :58100
make web-dev    # next dev :3000, /api proxy sang :58100
make test       # toàn bộ kiểm tra: API (trong docker) và web
make backup     # pg_dump vào backups/
```

## Cấu trúc

| Path | Nội dung |
| --- | --- |
| `apps/api` | FastAPI theo clean architecture: `app/shared` (nhân dùng chung) và `app/modules/<context>` chia 4 tầng domain / application / infrastructure / interface, cộng `worker`, `seed`, `migrations`, `tests` |
| `apps/web` | Next.js App Router: `app` (route mỏng), `components/{ui,common,layout,page-components}`, `hooks/{common,react-query,page-hooks}`, `services`, `stores`, `lib` |
| `infra/` | Caddyfile |
| `scripts/` | `verify.sh` (chạy test), `aidlc` + `gen_plan.py` + `close_ticket.sh` (kế hoạch), `golden_live.py` (chạy bộ đề chuẩn qua stack thật) |
| `.ai/` | Bản đồ kiến trúc, roadmap, kế hoạch từng feature và final review |

Tám bounded context: `identity`, `academic`, `taxonomy`, `bank`, `ingestion`, `assessment`, `analytics`, `audit`.
Chi tiết và luật phụ thuộc nằm ở [`.ai/architecture.md`](.ai/architecture.md).

## Quy ước API

- Danh sách: `POST /api/<resource>/search` với `{page, limit, q?, sort?, filters?}` → `{data, total, page, limit}`.
  Bộ lọc theo kiểu cột: chữ `* = + - !`, số và ngày `= < <= > >=` hoặc khoảng `from`/`to`, enum nhận danh sách.
- Lỗi: `{code, message, details: {fields?, requestId}}` kèm header `X-Request-Id`.
- Thời gian lưu và trả theo UTC; ngày tính theo giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- Đăng nhập bằng `mã tổ chức + tên đăng nhập + mật khẩu`, phiên giữ trong cookie httpOnly.

Tài liệu API tự sinh: http://localhost:8088/api/docs

## Phát triển

- Quy ước dành cho người và cho agent: [`AGENTS.md`](AGENTS.md), [`apps/api/AGENTS.md`](apps/api/AGENTS.md),
  [`apps/web/AGENTS.md`](apps/web/AGENTS.md). Công thức cho từng loại việc: [`.agents/skills/`](.agents/skills).
- Cách đóng góp, quy ước commit và checklist trước khi gửi: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Ranh giới tầng được lint: `lint-imports` (API) và ESLint (web) sẽ fail nếu import sai tầng.

## Build multi-arch

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t examind-api apps/api
docker buildx build --platform linux/amd64,linux/arm64 -t examind-web apps/web
```
