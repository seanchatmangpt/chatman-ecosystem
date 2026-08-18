#!/usr/bin/env bash
# Snapshots real facts from the live /Users/sac/ggen-marketplace checkout into
# facts.json for the Docker image, AND snapshots a real, already-compiled `ggen`
# binary that has the `pack list`/`pack query` subcommands this service's app.py
# shells out to.
#
# Why a workspace release build, not the cargo-installed binary on PATH
# ------------------------------------------------------------------------
# Confirmed this session: the cargo-installed `ggen` on this host's PATH
# (/Users/sac/.local/bin/ggen, version 26.8.8) does NOT have `pack query`
# ("unrecognized subcommand 'query'") -- it predates that verb. The workspace
# checkout at /Users/sac/ggen (26.8.12, `crates/ggen-cli/src/cmds/pack.rs`) does.
# So this script builds a real release binary from that live workspace source
# (`cargo build --release -p ggen-cli-lib --locked`, same crate the ggen/
# service's own Dockerfile builder stage targets) and snapshots the result,
# rather than trusting whatever happens to be on PATH.
set -euo pipefail

REPO="/Users/sac/ggen-marketplace"
GGEN_REPO="/Users/sac/ggen"
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$SELF_DIR/facts.json"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR: $REPO is not a git checkout on this host" >&2
  exit 1
fi

# Build (or reuse an already-built) release ggen binary from the live ggen workspace,
# then snapshot it into this service's build context -- same "COPY a build-time
# snapshot of the host, the running container never touches the host repo" convention
# services/ggen/prep.sh already uses for ggen-bin.
BUILT_BIN="$GGEN_REPO/target/release/ggen"
if [ ! -x "$BUILT_BIN" ]; then
  echo "building release ggen-cli-lib from $GGEN_REPO (this can take a while)..." >&2
  (cd "$GGEN_REPO" && cargo build --release -p ggen-cli-lib --locked)
fi

if [ -x "$BUILT_BIN" ]; then
  # Not snapshotted into this service's own build context as a binary: it is a macOS
  # Mach-O executable (confirmed this pass -- "Exec format error" when run directly
  # inside a python:3.12-slim Linux container), so the Dockerfile instead compiles a
  # Linux binary from source in its own builder stage (COPY ggen/ggen-src/). This
  # local build is used only to derive the real facts below and to smoke-test the
  # CLI contract on the host before containerizing.
  BIN_VERSION="$("$BUILT_BIN" --version 2>/dev/null | head -1 | awk '{print $2}' || true)"
  PACK_QUERY_PRESENT="false"
  if "$BUILT_BIN" pack --help 2>/dev/null | grep -qE '^\s*query\s'; then
    PACK_QUERY_PRESENT="true"
  fi
  echo "host release build ($BIN_VERSION, pack query present: $PACK_QUERY_PRESENT) confirmed at $BUILT_BIN"
else
  echo "ERROR: release build did not produce $BUILT_BIN" >&2
  exit 1
fi

# The `ggen-cli-lib` crate build.rs/const embeds pack catalog JSON via
# `include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../packs/<pack>/catalog/*.json"))`
# -- confirmed by a real failed Docker build this pass (missing
# packs/fortune5-deployment-blocks-pack/catalog/fortune5-bblocks.json). The sibling
# services/ggen/ggen-src/ snapshot lacks a top-level packs/ dir, so this service snapshots
# the real /Users/sac/ggen/packs/ (16MB) alongside it for the builder stage to COPY in.
GGEN_PACKS_SRC="$GGEN_REPO/packs"
rm -rf "$SELF_DIR/ggen-packs-src"
if [ -d "$GGEN_PACKS_SRC" ]; then
  cp -R "$GGEN_PACKS_SRC" "$SELF_DIR/ggen-packs-src"
  echo "snapshotted $GGEN_PACKS_SRC ($(du -sh "$SELF_DIR/ggen-packs-src" | cut -f1)) -> $SELF_DIR/ggen-packs-src"
else
  echo "ERROR: $GGEN_PACKS_SRC not found; cargo build would fail on missing include_str! targets" >&2
  exit 1
fi

# Snapshot the real ~/.ggen/packs registry this binary resolves by default (its
# try_get_packs_dir() home-directory fallback) into the build context, so the
# container has a real, non-empty pack registry to list/query without depending on
# host-only state at runtime.
PACKS_SRC="$HOME/.ggen/packs"
if [ -d "$PACKS_SRC" ]; then
  rm -rf "$SELF_DIR/packs-registry"
  mkdir -p "$SELF_DIR/packs-registry"
  cp "$PACKS_SRC"/*.toml "$SELF_DIR/packs-registry/" 2>/dev/null || true
  REGISTRY_PACK_COUNT="$(find "$SELF_DIR/packs-registry" -maxdepth 1 -name '*.toml' | wc -l | tr -d ' ')"
  echo "snapshotted $REGISTRY_PACK_COUNT real pack manifest(s) from $PACKS_SRC -> $SELF_DIR/packs-registry"
else
  mkdir -p "$SELF_DIR/packs-registry"
  REGISTRY_PACK_COUNT="0"
  echo "WARNING: $PACKS_SRC not found; packs-registry/ will be empty (real, not synthesized)." >&2
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

export PACK_COUNT NOTES REGISTRY_PACK_COUNT BIN_VERSION PACK_QUERY_PRESENT

python3 - "$OUT" "$GIT_HEAD" "$GIT_HEAD_SHORT" "$GIT_HEAD_SUBJECT" "$CHECKED_AT" <<'PYEOF'
import json, os, sys

out_path, git_head, git_head_short, git_head_subject, checked_at = sys.argv[1:6]
pack_count = int(os.environ.get("PACK_COUNT", "0"))
registry_pack_count = int(os.environ.get("REGISTRY_PACK_COUNT", "0"))
bin_version = os.environ.get("BIN_VERSION") or None
pack_query_present = os.environ.get("PACK_QUERY_PRESENT") == "true"
notes = []
if os.environ.get("NOTES"):
    notes.append(os.environ["NOTES"])
notes.append(
    "pack_count is the source-tree packs/ subdirectory count (marketplace repo layout, "
    "one dir per pack with its own ontology.ttl); registry_pack_count is the separate, "
    "smaller set of *.toml pack manifests this service's GET /packs and POST /query "
    "actually query, via ggen's try_get_packs_dir() resolver -- the two are not the "
    "same registry format and are not currently bridged."
)

facts = {
    "service": "ggen-marketplace-status",
    "repo": "ggen-marketplace",
    "git_head": git_head,
    "git_head_short": git_head_short,
    "git_head_subject": git_head_subject,
    "pack_count": pack_count,
    "registry_pack_count": registry_pack_count,
    "ggen_binary_version": bin_version,
    "pack_query_subcommand_present": pack_query_present,
    "checked_at": checked_at,
}
if notes:
    facts["notes"] = notes

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)
    f.write("\n")

print(json.dumps(facts, indent=2))
PYEOF
