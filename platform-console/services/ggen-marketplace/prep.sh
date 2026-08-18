#!/usr/bin/env bash
# Snapshots real facts from the live /Users/sac/ggen-marketplace checkout into
# facts.json for the Docker image. Filesystem count only -- no execution of
# any pack code.
set -euo pipefail

REPO="/Users/sac/ggen-marketplace"
OUT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/facts.json"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR: $REPO is not a git checkout on this host" >&2
  exit 1
fi

cd "$REPO"

GIT_HEAD="$(git log -1 --format=%H)"
GIT_HEAD_SHORT="$(git log -1 --format=%h)"
GIT_HEAD_SUBJECT="$(git log -1 --format=%s)"
CHECKED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [ -d packs ]; then
  PACK_COUNT="$(ls -1 packs/ | wc -l | tr -d ' ')"
  NOTES=""
else
  PACK_COUNT="0"
  NOTES="packs/ directory not found; pack_count is 0, not a real scan"
fi

export PACK_COUNT NOTES

python3 - "$OUT" "$GIT_HEAD" "$GIT_HEAD_SHORT" "$GIT_HEAD_SUBJECT" "$CHECKED_AT" <<'PYEOF'
import json, os, sys

out_path, git_head, git_head_short, git_head_subject, checked_at = sys.argv[1:6]
pack_count = int(os.environ.get("PACK_COUNT", "0"))
notes = []
if os.environ.get("NOTES"):
    notes.append(os.environ["NOTES"])

facts = {
    "service": "ggen-marketplace-status",
    "repo": "ggen-marketplace",
    "git_head": git_head,
    "git_head_short": git_head_short,
    "git_head_subject": git_head_subject,
    "pack_count": pack_count,
    "checked_at": checked_at,
}
if notes:
    facts["notes"] = notes

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)
    f.write("\n")

print(json.dumps(facts, indent=2))
PYEOF
