#!/usr/bin/env bash
# Snapshots real facts from the live /Users/sac/gymact checkout into
# facts.json for the Docker image. Shells out to the REAL installed CLI
# (the repo's .venv) to capture its actual `version` and `providers` output --
# these are not parsed from source, they are the live command output.
set -euo pipefail

REPO="/Users/sac/gymact"
OUT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/facts.json"
VENV_GYMACT="$REPO/.venv/bin/gymact"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR: $REPO is not a git checkout on this host" >&2
  exit 1
fi

cd "$REPO"

GIT_HEAD="$(git log -1 --format=%H)"
GIT_HEAD_SHORT="$(git log -1 --format=%h)"
GIT_HEAD_SUBJECT="$(git log -1 --format=%s)"
CHECKED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PYPROJECT_VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/version = "(.*)"/\1/' || true)"

CLI_VERSION=""
PROVIDERS_JSON=""
NOTES=""

if [ -x "$VENV_GYMACT" ]; then
  CLI_VERSION="$("$VENV_GYMACT" version 2>&1 || true)"
  PROVIDERS_JSON="$("$VENV_GYMACT" providers 2>&1 || true)"
else
  NOTES="gymact CLI not found at $VENV_GYMACT; cli_version/providers omitted"
fi

export PYPROJECT_VERSION CLI_VERSION PROVIDERS_JSON NOTES

python3 - "$OUT" "$GIT_HEAD" "$GIT_HEAD_SHORT" "$GIT_HEAD_SUBJECT" "$CHECKED_AT" <<'PYEOF'
import json, os, sys

out_path, git_head, git_head_short, git_head_subject, checked_at = sys.argv[1:6]
pyproject_version = os.environ.get("PYPROJECT_VERSION") or None
cli_version = os.environ.get("CLI_VERSION") or None
providers_raw = os.environ.get("PROVIDERS_JSON") or None
notes = []
if os.environ.get("NOTES"):
    notes.append(os.environ["NOTES"])

facts = {
    "service": "gymact-status",
    "repo": "gymact",
    "git_head": git_head,
    "git_head_short": git_head_short,
    "git_head_subject": git_head_subject,
    "pyproject_version": pyproject_version,
    "checked_at": checked_at,
}

if cli_version is not None:
    facts["installed_cli_version"] = cli_version
else:
    notes.append("installed_cli_version omitted: gymact CLI unavailable at build time")

if providers_raw:
    try:
        parsed = json.loads(providers_raw)
        facts["providers"] = parsed
    except json.JSONDecodeError:
        notes.append("providers command output was not valid JSON; omitted rather than guessed")
else:
    notes.append("providers omitted: gymact CLI unavailable at build time")

if pyproject_version and cli_version and pyproject_version != cli_version:
    notes.append(
        f"discrepancy: pyproject.toml declares version {pyproject_version} but the "
        f"installed CLI reports {cli_version}; both reported as separate real facts"
    )

if notes:
    facts["notes"] = notes

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)
    f.write("\n")

print(json.dumps(facts, indent=2))
PYEOF
