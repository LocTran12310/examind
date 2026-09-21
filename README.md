# Examind

Quản lý ngân hàng câu hỏi, đề ôn luyện và đề ôn tập cá nhân hóa cho trung tâm/giáo viên và học sinh.
Toàn bộ chạy self-host bằng Docker Compose (Postgres + pgvector, MinIO, FastAPI, Next.js, Caddy; Ollama ở các feature sau).

## Chạy nhanh

```bash
cp .env.example .env
docker compose up -d --build --wait
open http://localhost:8088/login     # tổ chức: system · admin / admin12345 (bắt đổi mật khẩu)
```

## Dev

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait postgres minio   # PG :55442, MinIO :59100
cd apps/api && uv run alembic upgrade head && uv run python -m app.seed.bootstrap && uv run uvicorn app.main:app --reload --port 58100
cd apps/web && pnpm dev                                                                         # :3000, /api proxied to :58100
./scripts/verify.sh apps/api/tests apps/web/src                                                 # tests
```

## Cấu trúc

| Path | Nội dung |
|---|---|
| `apps/api` | FastAPI + SQLAlchemy + Alembic (`app/core`, `models`, `schemas`, `services`, `routers`, `seed`, `worker`, `ingestion`) |
| `apps/web` | Next.js App Router + Tailwind |
| `infra/` | Caddyfile, backup/deploy scripts |
| `.ai/` | Kế hoạch AI-DLC: roadmap, architecture map, từng feature (intent → requirements → design → UoW/tickets) |

## Build multi-arch

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t examind-api apps/api
docker buildx build --platform linux/amd64,linux/arm64 -t examind-web apps/web
```
