#!/usr/bin/env bash
# Snapshots real facts from the live /Users/sac/ggen checkout into facts.json
# for the Docker image. Reports the repo's workspace Cargo.toml version AND
# the installed binary's own --version output as two separate real facts --
# they are not currently the same value on this host, and this script must
# not silently pick one.
set -euo pipefail

REPO="/Users/sac/ggen"
OUT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/facts.json"
BIN="$(command -v ggen || true)"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR: $REPO is not a git checkout on this host" >&2
  exit 1
fi

cd "$REPO"

GIT_HEAD="$(git log -1 --format=%H)"
GIT_HEAD_SHORT="$(git log -1 --format=%h)"
GIT_HEAD_SUBJECT="$(git log -1 --format=%s)"
CHECKED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

WORKSPACE_CARGO_VERSION="$(grep -m1 '^version' Cargo.toml | sed -E 's/version = "(.*)"/\1/' || true)"

INSTALLED_BINARY_VERSION=""
NOTES=""
SYNC_RUN_PRESENT="false"

if [ -n "$BIN" ]; then
  # `ggen --version` writes an INFO tracing line to stderr and the plain
  # version string to stdout; capture stdout only.
  INSTALLED_BINARY_VERSION="$("$BIN" --version 2>/dev/null | head -1 | awk '{print $2}' || true)"
  if "$BIN" sync --help 2>/dev/null | grep -qE '^\s*run\s'; then
    SYNC_RUN_PRESENT="true"
  fi
else
  NOTES="ggen binary not found on PATH; installed_binary_version/sync_run_subcommand_present omitted"
fi

export WORKSPACE_CARGO_VERSION INSTALLED_BINARY_VERSION NOTES SYNC_RUN_PRESENT

python3 - "$OUT" "$GIT_HEAD" "$GIT_HEAD_SHORT" "$GIT_HEAD_SUBJECT" "$CHECKED_AT" <<'PYEOF'
import json, os, sys

out_path, git_head, git_head_short, git_head_subject, checked_at = sys.argv[1:6]
workspace_version = os.environ.get("WORKSPACE_CARGO_VERSION") or None
installed_version = os.environ.get("INSTALLED_BINARY_VERSION") or None
sync_run_present = os.environ.get("SYNC_RUN_PRESENT") == "true"
notes = []
if os.environ.get("NOTES"):
    notes.append(os.environ["NOTES"])

facts = {
    "service": "ggen-status",
    "repo": "ggen",
    "git_head": git_head,
    "git_head_short": git_head_short,
    "git_head_subject": git_head_subject,
    "workspace_cargo_version": workspace_version,
    "installed_binary_version": installed_version,
    "sync_run_subcommand_present": sync_run_present,
    "checked_at": checked_at,
}

if workspace_version and installed_version and workspace_version != installed_version:
    notes.append(
        f"discrepancy: repo Cargo.toml workspace version is {workspace_version} but the "
        f"installed binary reports {installed_version}; both reported as separate real facts"
    )

if notes:
    facts["notes"] = notes

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)
    f.write("\n")

print(json.dumps(facts, indent=2))
PYEOF
