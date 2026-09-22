# Đóng góp vào Examind

Dự án chạy solo, nhưng mọi thay đổi vẫn đi theo cùng một đường: có kế hoạch trên đĩa, có test thật, có bản ghi
quyết định. Tài liệu quy ước cho cả người và agent nằm ở [`AGENTS.md`](AGENTS.md) (và bản riêng của
[api](apps/api/AGENTS.md), [web](apps/web/AGENTS.md)).

## Chuẩn bị

```bash
cp .env.example .env
make dev            # Postgres :55442, MinIO :59100
cd apps/api && uv sync
cd ../web && pnpm install
```

Cần: Docker, `uv`, Node 20+ với `pnpm`. Không cần cài Postgres hay MinIO ở máy.

## Vòng làm việc

1. **Nhánh riêng:** `feat/<slug>`, `fix/<slug>` hoặc `refactor/<slug>`. Không commit thẳng vào `main`.
2. **Có kế hoạch nếu là feature:** xem skill [`feature-plan`](.agents/skills/feature-plan/SKILL.md). Sửa lỗi nhỏ
   thì không cần, nhưng vẫn phải có test tái hiện lỗi trước khi sửa.
3. **Viết code theo tầng:** API `interface → infrastructure → application → domain`; web
   route → page component → page hook → query hook → service. Lint sẽ chặn nếu import sai.
4. **Test cùng lúc:** handler test với port giả (`apps/api/tests/unit`) và test HTTP theo resource; web dùng
   `renderWithQuery` + `mockFetch`.
5. **Chạy kiểm tra:** `make test` (hoặc `make test-api` / `make test-web`). Đụng vào pipeline đọc đề thì chạy thêm
   `make golden EXAMIN_DIR=…` và số liệu phải giữ nguyên.
6. **Commit:** `type(scope): tóm tắt` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Thân commit nói **vì sao**,
   không kể lại diff. Không commit khi suite đang đỏ.

## Checklist trước khi gửi

- [ ] `make lint` sạch (ruff, lint-imports, eslint)
- [ ] `make test` xanh; nếu có bỏ qua test nào thì nói rõ lý do
- [ ] Đổi schema: có revision Alembic và `alembic check` không lệch (`make test-api` đã bao gồm)
- [ ] Đổi contract API: đã sửa mọi chỗ gọi ở web và test tương ứng
- [ ] Có thay đổi giao diện: đã mở trình duyệt xem thật, nói rõ đã xem gì
- [ ] Quyết định mới được ghi vào ADR trong `.ai/features/<feature>/03-logical-design.md`

## Không làm

- Sửa file trong `apps/web/src/components/ui` bằng tay (đó là output của shadcn CLI).
- Nới lỏng luật lint để code lọt qua.
- Xoá hoặc ghi đè dữ liệu thật (drop, truncate, xoá hàng loạt, xoá object MinIO, viết lại lịch sử git) khi chưa
  được yêu cầu đúng việc đó. Sao lưu trước bằng `make backup`.
- Commit `.env`, dump trong `backups/`, hay bất kỳ khoá bí mật nào.
