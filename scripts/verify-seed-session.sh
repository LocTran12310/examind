#!/usr/bin/env bash
# The login form has three fields (tổ chức, tên đăng nhập, mật khẩu) and the verification runner's `form`
# recipe fills two. The app prefills the org code from localStorage, so the run starts from a browser that
# already remembers it: this writes that one key into the session state the runner loads.
#   scripts/verify-seed-session.sh [env-name] [org-code] [url]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_NAME="${1:-local}"
ORG="${2:-$(grep -E '^LOCAL_ORG=' "$ROOT/.ai/credentials.env" 2>/dev/null | cut -d= -f2- || echo trungtama)}"
URL="${3:-$(grep -E '^LOCAL_URL=' "$ROOT/.ai/credentials.env" 2>/dev/null | cut -d= -f2- || echo http://localhost:8088)}"
mkdir -p "$ROOT/.ai/.auth"
cat > "$ROOT/.ai/.auth/$ENV_NAME.json" <<JSON
{
  "cookies": [],
  "origins": [
    { "origin": "$URL", "localStorage": [{ "name": "examind.org_code", "value": "$ORG" }] }
  ]
}
JSON
echo "seeded $ROOT/.ai/.auth/$ENV_NAME.json ($ORG @ $URL)"
