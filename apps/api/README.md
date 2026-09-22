# examind-api

FastAPI + SQLAlchemy 2 + Alembic, Postgres (ltree, pgvector) và MinIO. Cùng package còn một worker xử lý
tài liệu. Python 3.12, quản lý phụ thuộc bằng `uv`.

## Chạy ở máy

```bash
make dev                     # Postgres :55442, MinIO :59100 (từ thư mục gốc)
cd apps/api
uv sync
uv run alembic upgrade head
uv run python -m app.seed.bootstrap
uv run uvicorn app.main:app --reload --port 58100      # docs: /api/docs
```

## Kiểm tra

```bash
uv run ruff check .          # style (uv run ruff check --fix . cho phần máy sửa được)
uv run lint-imports          # luật phụ thuộc giữa các tầng (.importlinter)
cd ../.. && ./scripts/verify.sh apps/api/tests          # toàn bộ suite, chạy trong image api-test
./scripts/verify.sh apps/api/tests/unit                 # chỉ handler test, không cần database
EXAMIN_DIR=<thư mục đề> ./scripts/verify.sh apps/api/tests/test_golden_official.py
```

## Cấu trúc

```
app/main.py            composition root: middleware, ánh xạ lỗi, actor resolver, nối adapter giữa module, router
app/metadata.py        toàn bộ Table + ORM mapping (Alembic, seed và test đều import)
app/shared/            nhân dùng chung: domain errors, search contract, unit of work, Actor, SQL search,
                       config, storage, logging, lịch nghiệp vụ, request id, dependency xác thực
app/modules/<context>/ identity · academic · taxonomy · bank · ingestion · assessment · analytics · audit
    domain/            entity dataclass, value object, quy tắc thuần, port (Protocol)
    application/       commands/ · queries/ (mỗi file một handler), dto.py, api.py (những gì module khác gọi được)
    infrastructure/    orm.py, repositories.py, read_models.py, adapters/
    interface/         router.py, schemas.py, deps.py
app/worker/            vòng lặp job; mỗi loại job gọi một command
app/seed/              tổ chức hệ thống, super admin, dữ liệu tham chiếu
migrations/versions/   revision Alembic
tests/                 test HTTP theo resource, tests/unit/ chạy handler với port giả, test kiến trúc và drift
```

Luật phụ thuộc, cách thêm endpoint và các quy ước khác: [`AGENTS.md`](AGENTS.md) và
[`../../.ai/architecture.md`](../../.ai/architecture.md).
