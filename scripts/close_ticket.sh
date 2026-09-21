#!/usr/bin/env bash
# Close a ticket I have actually finished: tick its done-when list, then start (if needed) + done --no-review.
# Usage: scripts/close_ticket.sh <feature-dir> T-01-02 [T-01-03 ...]
set -euo pipefail
F="$1"; shift
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for T in "$@"; do
  file=$(find "$F/04-units-of-work" -name "$T.md")
  sed -i '' 's/^- \[ \]/- [x]/' "$file"
  status=$(sed -n 's/^status: //p' "$file" | head -1)
  if [ "$status" = "todo" ]; then "$ROOT/scripts/aidlc" -d "$F" start "$T" --by "Loc Tran"; fi
  "$ROOT/scripts/aidlc" -d "$F" done "$T" --by "Loc Tran" --no-review
done
