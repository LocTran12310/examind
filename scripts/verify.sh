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
  # ADR-06 (exam-ingestion): API tests run inside the api image (pandoc, tesseract available).
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait postgres minio >/dev/null
  docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile test build -q api-test >/dev/null
  docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile test run --rm -T api-test \
    pytest -q -p no:cacheprovider "${api_tests[@]}" || status=$?
fi
if ((${#web_tests[@]})); then
  (cd apps/web && pnpm exec vitest run "${web_tests[@]}") || status=$?
fi
exit $status
