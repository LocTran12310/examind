#!/usr/bin/env bash
# Run the tests named on the command line; used by `aidlc submit/done` (evidence block).
#   apps/api/...  → pytest against the dev-compose postgres/minio
#   apps/web/...  → vitest
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

api_tests=(); web_tests=()
for t in "$@"; do
  case "$t" in
    apps/api/*) api_tests+=("${t#apps/api/}") ;;
    apps/web/*) web_tests+=("${t#apps/web/}") ;;
    *) echo "verify.sh: don't know how to run $t" >&2; exit 2 ;;
  esac
done

status=0
if ((${#api_tests[@]})); then
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait postgres minio >/dev/null
  (
    cd apps/api
    export TEST_DATABASE_URL="postgresql+psycopg://examind:examind@localhost:${PG_PORT:-55442}/examind_test"
    export S3_ENDPOINT="http://localhost:${MINIO_PORT:-59100}"
    uv run --quiet pytest -q "${api_tests[@]}"
  ) || status=$?
fi
if ((${#web_tests[@]})); then
  (cd apps/web && pnpm exec vitest run "${web_tests[@]}") || status=$?
fi
exit $status
