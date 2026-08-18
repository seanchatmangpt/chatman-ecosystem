#!/usr/bin/env bash
# Snapshots real facts from the live /Users/sac/autofde-lab checkout into
# facts.json, which is then COPYed into the Docker image at build time.
# Run this from a host that has /Users/sac/autofde-lab checked out, BEFORE
# `docker build`. No field here is invented -- only what is directly readable
# from the repo's git history and Justfile.
set -euo pipefail

REPO="/Users/sac/autofde-lab"
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

# Real, literal recipe names found in the Justfile (top-level `name:` lines).
export ALL_TARGETS="$(grep -oE '^[a-zA-Z0-9_-]+:' Justfile | sed 's/:$//' | sort -u || true)"

python3 - "$OUT" "$GIT_HEAD" "$GIT_HEAD_SHORT" "$GIT_HEAD_SUBJECT" "$CHECKED_AT" <<'PYEOF'
import json, os, sys

out_path, git_head, git_head_short, git_head_subject, checked_at = sys.argv[1:6]
all_targets = set(x for x in os.environ.get("ALL_TARGETS", "").splitlines() if x)

wanted = ["test", "test-full", "test-level4", "test-level4-full"]
present = [t for t in wanted if t in all_targets]
missing = [t for t in wanted if t not in all_targets]

facts = {
    "service": "autofde-lab-status",
    "repo": "autofde-lab",
    "git_head": git_head,
    "git_head_short": git_head_short,
    "git_head_subject": git_head_subject,
    "justfile_targets_present": present,
    "checked_at": checked_at,
}
if missing:
    facts["notes"] = f"expected Justfile targets not found: {missing}"

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)
    f.write("\n")

print(json.dumps(facts, indent=2))
PYEOF
