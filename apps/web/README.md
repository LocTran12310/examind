# examind-web

Next.js 15 App Router, React 19, Tailwind v4, shadcn/ui, TanStack Query + Table, zustand, vitest.

## Chạy ở máy

```bash
make dev && make api-dev     # từ thư mục gốc: hạ tầng + API trên :58100
cd apps/web
pnpm install
pnpm dev                     # :3000, /api proxy sang :58100 (next.config.ts)
```

## Kiểm tra

```bash
pnpm typecheck
NODE_OPTIONS=--max-old-space-size=6144 pnpm lint    # eslint, gồm cả luật ranh giới tầng
pnpm test                                           # vitest
pnpm build
```

## Cấu trúc

```
src/app/                                  chỉ route: page.tsx render đúng một page component
src/components/ui/                        file do shadcn CLI sinh, không sửa tay
src/components/common/<Name>/             component dùng chung (DataTable, FormDialog, DatePicker, QuestionView…)
src/components/layout/<Name>/             Providers, AppShell, sidebar, switcher, theme
src/components/page-components/<Page>/    <Page>Page.tsx và component riêng của trang đó
src/hooks/common/ react-query/ page-hooks/  state URL của bảng · hook gọi API · logic từng trang
src/services/<module>.service.ts          nơi duy nhất gọi HTTP
src/stores/                               zustand, chỉ giữ state giao diện
src/constants/ dtos/ interfaces/ types/   hằng số, body request, entity, union
src/lib/common/ page-libs/                http, query client, search body, ngày giờ… · hàm thuần của một trang
```

Luồng dữ liệu: URL (bộ lọc, sắp xếp, trang) → `useTableQuery` → `toSearchBody` → `useXxxSearchQuery` →
service → `POST /api/x/search`. React Query giữ server state; mutation invalidate `<ENTITY>_KEYS.ALL`.

Quy ước và cách thêm một màn hình: [`AGENTS.md`](AGENTS.md) và [`../../.ai/architecture.md`](../../.ai/architecture.md).
