# Examind — the commands the project is run and checked with.
# `make` alone lists them.
COMPOSE      := docker compose
COMPOSE_DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml
API_PORT     ?= 58100
EXAMIN_DIR   ?=

.DEFAULT_GOAL := help
VERIFY       := python3 $(HOME)/.claude/skills/ai-dlc-verify/scripts/verify.py
VERIFY_CHECK := python3 $(HOME)/.claude/skills/ai-dlc-verify/scripts/evidence_check.py
export AIDLC_VERIFY_PYTHON ?= $(HOME)/.venvs/aidlc-verify/bin/python

.PHONY: help up down logs ps dev api-dev web-dev migrate revision seed test test-api test-web test-unit \
        lint lint-api lint-web fix typecheck build golden backup verify verify-doctor verify-check

help: ## Show this list
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'

## ----------------------------------------------------------------- stack

up: ## Build and start the whole stack (http://localhost:8088)
	$(COMPOSE) up -d --build --wait

down: ## Stop the stack (volumes are kept)
	$(COMPOSE) down

ps: ## What is running
	$(COMPOSE) ps

logs: ## Follow the api and worker logs
	$(COMPOSE) logs -f api worker

dev: ## Postgres :55442 and MinIO :59100 for a local api/web
	$(COMPOSE_DEV) up -d --wait postgres minio

api-dev: dev ## uvicorn --reload on :$(API_PORT)
	cd apps/api && uv run alembic upgrade head && uv run python -m app.seed.bootstrap && \
		uv run uvicorn app.main:app --reload --port $(API_PORT)

web-dev: ## next dev on :3000 (/api proxied to :$(API_PORT))
	cd apps/web && pnpm install && pnpm dev

## ----------------------------------------------------------------- database

migrate: ## alembic upgrade head (local api, needs `make dev`)
	cd apps/api && uv run alembic upgrade head

revision: ## New Alembic revision: make revision m="what changed"
	@test -n "$(m)" || (echo 'usage: make revision m="what changed"' && exit 1)
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

seed: ## System org, super admin and reference data
	cd apps/api && uv run python -m app.seed.bootstrap

backup: ## pg_dump the running database into backups/
	@mkdir -p backups
	$(COMPOSE) exec -T postgres pg_dump -U $${POSTGRES_USER:-examind} -Fc $${POSTGRES_DB:-examind} \
		> backups/examind-$$(date +%Y%m%d%H%M).dump
	@ls -lh backups | tail -1

## ----------------------------------------------------------------- checks

test: test-api test-web ## Everything

test-api: lint-api ## ruff + lint-imports + the API suite (in the api-test image)
	./scripts/verify.sh apps/api/tests

test-unit: ## API handler tests only (fake ports, no database)
	./scripts/verify.sh apps/api/tests/unit

test-web: ## tsc + eslint + vitest
	cd apps/web && pnpm typecheck && NODE_OPTIONS=--max-old-space-size=6144 pnpm lint && pnpm test

golden: ## The 18 official papers: make golden EXAMIN_DIR=/path/to/papers
	@test -n "$(EXAMIN_DIR)" || (echo 'usage: make golden EXAMIN_DIR=/path/to/papers' && exit 1)
	EXAMIN_DIR=$(EXAMIN_DIR) ./scripts/verify.sh apps/api/tests/test_golden_official.py

lint: lint-api lint-web ## Style and layer rules, both sides

lint-api: ## ruff + the import contracts
	cd apps/api && uv run ruff check . && uv run lint-imports

lint-web: ## eslint (import boundaries included)
	cd apps/web && NODE_OPTIONS=--max-old-space-size=6144 pnpm lint

typecheck: ## tsc --noEmit
	cd apps/web && pnpm typecheck

fix: ## ruff --fix on the API (mechanical lint fixes; there is no formatter, see AGENTS.md)
	cd apps/api && uv run ruff check --fix .

## ----------------------------------------------------------------- browser verification

verify-doctor: ## Which rung verification is on: make verify-doctor f=.ai/features/<slug>
	@test -n "$(f)" || (echo 'usage: make verify-doctor f=.ai/features/<slug>' && exit 1)
	$(VERIFY) $(f) --doctor

verify: ## Walk a feature's 07-verification.md in a browser: make verify f=.ai/features/<slug>
	@test -n "$(f)" || (echo 'usage: make verify f=.ai/features/<slug>' && exit 1)
	./scripts/verify-seed-session.sh >/dev/null
	$(VERIFY) $(f) --write

verify-check: ## Check the evidence backs the claims: make verify-check f=.ai/features/<slug>
	@test -n "$(f)" || (echo 'usage: make verify-check f=.ai/features/<slug>' && exit 1)
	$(VERIFY_CHECK) $(f)

build: ## Production build of the web app
	cd apps/web && pnpm build
