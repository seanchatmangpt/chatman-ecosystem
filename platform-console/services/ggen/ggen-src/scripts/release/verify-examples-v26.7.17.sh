#!/usr/bin/env bash
# scripts/release/verify-examples-v26.7.17.sh
#
# Example Verification Harness (v26.7.17 release DoD).
#
# Reads the canonical examples manifest (default: examples/examples.toml), runs the
# declared verification command for every non-excluded entry against a throwaway copy
# of that example, and writes a JSON + Markdown report under
# target/ggen-release/v26.7.17/reports/.
#
# USAGE
#   scripts/release/verify-examples-v26.7.17.sh [MANIFEST_PATH] [EXAMPLES_ROOT]
#
#   MANIFEST_PATH   default: <repo_root>/examples/examples.toml
#   EXAMPLES_ROOT   default: <repo_root>/examples (only used to sanity-check that a
#                   manifest entry's declared path resolves under the repo)
#
# If MANIFEST_PATH does not exist, this script prints a clear SKIP message, still
# writes an (empty) JSON + Markdown report so downstream tooling always has something
# to read, and exits 0. This is deliberate: examples/examples.toml is expected to land
# in a later task (see examples/examples.inventory.toml's own header comment), and this
# harness must be safe to run, and safe to wire into CI, before that happens.
#
# ---------------------------------------------------------------------------
# Expected examples.toml schema (this harness's contract -- update both together)
# ---------------------------------------------------------------------------
#   [[examples]]
#   name    = "simple-project"            # required, unique
#   path    = "examples/simple-project"   # required, repo-root-relative
#   kind    = "generated-project"         # required: "generated-project" | "rust-example"
#   status  = "ACTIVE"                    # optional, default "ACTIVE".
#                                          # "ARCHIVED" / "DOCUMENTATION_ONLY" are excluded
#                                          # from verification entirely (never run, never
#                                          # scored PASS/BLOCKED/etc -- they show up only in
#                                          # the report's separate "excluded" list).
#   receipt_workflow = false              # optional bool. If true, `ggen receipt verify`
#                                          # is run after the real (non-dry-run) sync.
#   expect_refusal_pattern = ""           # optional extended-regex (grep -E). If the
#                                          # verification command exits non-zero AND its
#                                          # combined stdout+stderr matches this pattern,
#                                          # the entry is scored TYPED_REFUSAL_AS_DESIGNED
#                                          # instead of BLOCKED. Absent -> any non-zero exit
#                                          # is BLOCKED (no assumed-designed refusals).
#   cargo_example_name = ""               # optional, rust-example only. Overrides the
#                                          # `--example <name>` argument to `cargo build`
#                                          # when it differs from `name` (e.g. `name` carries
#                                          # a `.rs` suffix or a disambiguating prefix).
#   notes = ""                            # optional, free text, carried into the report only
#
# ---------------------------------------------------------------------------
# Per-entry verification command, by kind
# ---------------------------------------------------------------------------
#   generated-project:
#     1. `ggen sync run --dry-run --format json` in a clean `cp -r` copy of the example
#        directory (never the real examples/<name>/ tree).
#     2. Verify it caused zero filesystem mutation (sha256 digest of the copy, before vs.
#        after).
#     3. If (1)+(2) hold: `ggen sync run --format json` (real, writes files), then run it
#        again to check idempotency -- both the second run's own `.written == []` self-report
#        AND an independent filesystem digest equality between the two real runs must hold.
#     4. If `receipt_workflow = true`: `ggen receipt verify` in the same copy.
#
#   rust-example:
#     `cargo build --example <cargo_example_name or name>` run from the real repo root.
#     Deliberately NOT run against an isolated copy: `cargo build --example <name>`
#     resolves against the workspace's own Cargo.toml manifest graph (see root Cargo.toml's
#     `[[example]]` table), and there is no way to redirect that resolution into a `cp -r`
#     copy without duplicating the entire workspace. `cargo build` also never mutates
#     `examples/` -- it only writes into `target/` -- so the isolation that matters for
#     generated-project entries (protecting a real project tree from `ggen sync run`
#     writes) has nothing to protect here. Dry-run / zero-mutation / idempotency checks
#     (steps 7-9 above) are therefore not applicable to this kind and are recorded as
#     not-checked in the report, not silently assumed to pass.
#
# ---------------------------------------------------------------------------
# Report status vocabulary (one of these per non-excluded example)
# ---------------------------------------------------------------------------
#   PASS                       All applicable checks for this entry's kind passed.
#   TYPED_REFUSAL_AS_DESIGNED  Verification command exited non-zero, but the manifest
#                              declared `expect_refusal_pattern` and the failure output
#                              matched it -- a deliberate, documented gate, not a break.
#   BLOCKED                    Verification command failed (and no matching expected
#                              refusal was declared), OR a zero-mutation / idempotency /
#                              receipt-verify check failed.
#   INFRASTRUCTURE_BLOCKED     The harness itself could not set up preconditions for this
#                              entry (declared path missing, ggen.toml missing for a
#                              generated-project entry, the ggen binary failed to build,
#                              or a receipt_workflow was declared for a rust-example entry
#                              which has no project directory to verify a receipt against).
#                              Distinguishes "the example broke" from "the harness/build
#                              environment broke".
#   UNSUPPORTED                The manifest declared a `kind` this harness version does not
#                              implement.
#
# Excluded entries (status ARCHIVED / DOCUMENTATION_ONLY) are never run and never given one
# of the statuses above; they are listed separately in the report under "excluded".

set -uo pipefail
# Deliberately NOT `set -e`: this harness's entire job is to keep going after a single
# example's verification command fails, and record that failure -- an early exit here
# would silently truncate the report instead.

# ---------------------------------------------------------------------------
# 0. Paths, tool preflight, timestamps
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MANIFEST="${1:-$REPO_ROOT/examples/examples.toml}"
EXAMPLES_ROOT="${2:-$REPO_ROOT/examples}"

RELEASE_TAG="v26.7.17"
RELEASE_DIR="$REPO_ROOT/target/ggen-release/$RELEASE_TAG"
REPORTS_DIR="$RELEASE_DIR/reports"
JSON_REPORT="$REPORTS_DIR/examples-report.json"
MD_REPORT="$REPORTS_DIR/examples-report.md"

# Per-subprocess timeout (dry-run / real sync / cargo build / receipt verify each get
# their own budget). Override with VERIFY_EXAMPLES_TIMEOUT_SECS for slow machines/CI.
STEP_TIMEOUT="${VERIFY_EXAMPLES_TIMEOUT_SECS:-120}"

mkdir -p "$REPORTS_DIR"

log() { echo "[verify-examples] $*"; }
warn() { echo "[verify-examples] WARN: $*" >&2; }

for tool in python3 jq sha256sum find cp mktemp; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "BUILD_BROKEN: required tool '$tool' not found on PATH" >&2
    exit 1
  fi
done

RUN_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_STARTED_EPOCH="$(date +%s)"

# ---------------------------------------------------------------------------
# 1. Graceful skip: examples.toml has not landed yet
# ---------------------------------------------------------------------------
if [ ! -f "$MANIFEST" ]; then
  log "SKIP: manifest not found at $MANIFEST"
  log "SKIP: examples/examples.toml has not landed yet -- nothing to verify."
  log "SKIP: writing an empty report so downstream tooling has something to read."

  MANIFEST="$MANIFEST" RUN_STARTED_AT="$RUN_STARTED_AT" \
  JSON_REPORT="$JSON_REPORT" MD_REPORT="$MD_REPORT" \
  python3 - <<'PY'
import json
import os

manifest = os.environ["MANIFEST"]
started = os.environ["RUN_STARTED_AT"]
json_path = os.environ["JSON_REPORT"]
md_path = os.environ["MD_REPORT"]

report = {
    "harness": "verify-examples-v26.7.17.sh",
    "started_at": started,
    "manifest": manifest,
    "manifest_found": False,
    "summary": {
        "total": 0,
        "excluded": 0,
        "PASS": 0,
        "TYPED_REFUSAL_AS_DESIGNED": 0,
        "BLOCKED": 0,
        "INFRASTRUCTURE_BLOCKED": 0,
        "UNSUPPORTED": 0,
    },
    "excluded": [],
    "results": [],
}
with open(json_path, "w") as f:
    json.dump(report, f, indent=2)
    f.write("\n")

with open(md_path, "w") as f:
    f.write("# Example Verification Report (v26.7.17)\n\n")
    f.write(f"Started: {started}\n\n")
    f.write(f"**SKIPPED** -- manifest `{manifest}` not found. No examples were verified.\n")

print(f"wrote {json_path}")
print(f"wrote {md_path}")
PY

  exit 0
fi

# ---------------------------------------------------------------------------
# 2. Parse the manifest (bash+embedded-python3+tomllib, matching
#    scripts/ci/guard-publish-standing.sh's existing pattern for TOML in this repo)
# ---------------------------------------------------------------------------
WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ggen-verify-examples.XXXXXX")"
cleanup() {
  if [ -n "${VERIFY_EXAMPLES_KEEP_WORKDIR:-}" ]; then
    warn "VERIFY_EXAMPLES_KEEP_WORKDIR set -- leaving $WORK_ROOT on disk for inspection"
  else
    rm -rf "$WORK_ROOT"
  fi
}
trap cleanup EXIT

ENTRIES_JSON="$WORK_ROOT/entries.json"

if ! MANIFEST="$MANIFEST" ENTRIES_JSON="$ENTRIES_JSON" python3 - <<'PY'
import json
import os
import sys
import tomllib

manifest_path = os.environ["MANIFEST"]
out_path = os.environ["ENTRIES_JSON"]
EXCLUDE_STATUSES = {"ARCHIVED", "DOCUMENTATION_ONLY"}
KNOWN_KINDS = {"generated-project", "rust-example"}

with open(manifest_path, "rb") as f:
    data = tomllib.load(f)

entries = data.get("examples", [])
errors = []
seen = set()
out = []

for i, e in enumerate(entries):
    name = e.get("name")
    path = e.get("path")
    kind = e.get("kind")
    label = name if name else f"<examples[{i}]>"
    if not name or not path or not kind:
        errors.append(f"{label}: missing required field(s) among name/path/kind")
        continue
    if name in seen:
        errors.append(f"{name}: duplicate name")
    seen.add(name)

    status = str(e.get("status", "ACTIVE"))
    excluded = status in EXCLUDE_STATUSES

    out.append(
        {
            "name": name,
            "path": path,
            "kind": kind,
            "kind_known": kind in KNOWN_KINDS,
            "status_field": status,
            "excluded": excluded,
            "receipt_workflow": bool(e.get("receipt_workflow", False)),
            "expect_refusal_pattern": str(e.get("expect_refusal_pattern", "") or ""),
            "cargo_example_name": str(e.get("cargo_example_name", "") or ""),
            "notes": str(e.get("notes", "") or ""),
        }
    )

if errors:
    for err in errors:
        print(f"MANIFEST_ERROR: {err}", file=sys.stderr)
    sys.exit(1)

with open(out_path, "w") as f:
    json.dump(out, f)

excluded_count = sum(1 for x in out if x["excluded"])
print(f"Parsed {len(out)} entries from {manifest_path} ({excluded_count} excluded)")
PY
then
  echo "BUILD_BROKEN: failed to parse $MANIFEST -- see MANIFEST_ERROR lines above" >&2
  exit 1
fi

TOTAL_ENTRIES="$(jq 'length' "$ENTRIES_JSON")"
log "manifest parsed: $TOTAL_ENTRIES entries in $MANIFEST"

# ---------------------------------------------------------------------------
# 3. Build the ggen binary once (generated-project entries need it; a build failure
#    here is an INFRASTRUCTURE_BLOCKED condition for every generated-project entry,
#    not a per-example failure)
# ---------------------------------------------------------------------------
GGEN_BIN="$REPO_ROOT/target/debug/ggen"
GGEN_BUILD_LOG="$WORK_ROOT/ggen-build.log"
GGEN_BUILD_OK="true"

log "building ggen binary (cargo build -p ggen-cli-lib --bin ggen)..."
if ! (cd "$REPO_ROOT" && cargo build -p ggen-cli-lib --bin ggen) >"$GGEN_BUILD_LOG" 2>&1; then
  GGEN_BUILD_OK="false"
  warn "failed to build the ggen binary -- every generated-project entry will be INFRASTRUCTURE_BLOCKED"
  warn "build log: $GGEN_BUILD_LOG"
elif [ ! -x "$GGEN_BIN" ]; then
  GGEN_BUILD_OK="false"
  warn "cargo build succeeded but $GGEN_BIN is not an executable -- treating as a build failure"
fi

# ---------------------------------------------------------------------------
# 4. Helpers
# ---------------------------------------------------------------------------

# sha256 digest of an entire directory tree's file contents (order-independent).
# Used for the dry-run zero-mutation check: a dry run must not write anything at all,
# not even a receipt, so nothing is excluded here (confirmed empirically: a real
# `ggen sync run --dry-run` leaves `.ggen-v2/` untouched).
tree_digest() {
  local dir="$1"
  find "$dir" -type f -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}'
}

# Same, but excluding .ggen-v2/ (the BLAKE3 receipt chain: receipt.json +
# receipt-log.jsonl). Used for the real-sync idempotency check only. Confirmed
# empirically (2026-07-18): running `ggen sync run` twice on an unchanged manifest
# reports `.written == []` both times and leaves every declared generation-rule output
# file byte-identical, but .ggen-v2/receipt.json and receipt-log.jsonl legitimately
# differ on every run by design (each sync appends a new chained, timestamped receipt
# entry -- that is what "chained" means). Diffing the unfiltered whole-tree digest
# across two real runs would therefore flag every correctly-idempotent example as
# non-idempotent; this exclusion is what makes the digest check agree with the tool's
# own `.written` self-report instead of contradicting it for a reason that has nothing
# to do with the generated deliverables.
tree_digest_excluding_receipts() {
  local dir="$1"
  find "$dir" -type f -not -path '*/.ggen-v2/*' -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}'
}

# Names of every currently-exported GGEN_* env var, so subprocess runs never inherit
# this session's (or a developer's) ggen-specific state (signing keys, feature flags, ...).
# Populates the global UNSET_ARGS array directly (not via a printf/mapfile round-trip
# through a pipe: `printf '%s\0' "${args[@]}"` on an empty array still emits one empty
# field, which would otherwise turn into a stray `env ""` argument -- `env` treats a bare
# empty string as the command to run, not a no-op, and fails with exit 127).
declare -a UNSET_ARGS=()
compute_unset_args() {
  UNSET_ARGS=()
  local v
  while IFS= read -r v; do
    [ -n "$v" ] && UNSET_ARGS+=(-u "$v")
  done < <(compgen -e | grep '^GGEN_' || true)
}
compute_unset_args

RESULTS_FILE="$WORK_ROOT/results.jsonl"
: >"$RESULTS_FILE"

PASS_COUNT=0
REFUSAL_COUNT=0
BLOCKED_COUNT=0
INFRA_COUNT=0
UNSUPPORTED_COUNT=0
EXCLUDED_COUNT=0

emit_result() {
  # All args passed as --arg/--argjson pairs below; keeps quoting centralized in one place.
  local name="$1" path="$2" kind="$3" status="$4" reason="$5" verify_cmd="$6"
  local exit_code_json="$7" stdout_tail="$8" stderr_tail="$9" duration_s="${10}"
  local dry_run_checked="${11}" dry_run_zero_mutation="${12}"
  local digest_before="${13}" digest_after="${14}"
  local idempotency_checked="${15}" idempotency_ok="${16}"
  local receipt_checked="${17}" receipt_ok="${18}" tmp_dir="${19}"

  jq -nc \
    --arg name "$name" \
    --arg path "$path" \
    --arg kind "$kind" \
    --arg status "$status" \
    --arg reason "$reason" \
    --arg verify_command "$verify_cmd" \
    --argjson exit_code "$exit_code_json" \
    --arg stdout_tail "$stdout_tail" \
    --arg stderr_tail "$stderr_tail" \
    --argjson duration_seconds "$duration_s" \
    --argjson dry_run_checked "$dry_run_checked" \
    --argjson dry_run_zero_mutation "$dry_run_zero_mutation" \
    --arg digest_before "$digest_before" \
    --arg digest_after "$digest_after" \
    --argjson idempotency_checked "$idempotency_checked" \
    --argjson idempotency_ok "$idempotency_ok" \
    --argjson receipt_checked "$receipt_checked" \
    --argjson receipt_ok "$receipt_ok" \
    --arg tmp_dir "$tmp_dir" \
    '{name:$name, path:$path, kind:$kind, status:$status, reason:$reason,
      verify_command:$verify_command, exit_code:$exit_code,
      stdout_tail:$stdout_tail, stderr_tail:$stderr_tail,
      duration_seconds:$duration_seconds,
      dry_run_checked:$dry_run_checked, dry_run_zero_mutation:$dry_run_zero_mutation,
      digest_before:$digest_before, digest_after:$digest_after,
      idempotency_checked:$idempotency_checked, idempotency_ok:$idempotency_ok,
      receipt_checked:$receipt_checked, receipt_ok:$receipt_ok,
      tmp_dir:$tmp_dir}' >>"$RESULTS_FILE"

  case "$status" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    TYPED_REFUSAL_AS_DESIGNED) REFUSAL_COUNT=$((REFUSAL_COUNT + 1)) ;;
    BLOCKED) BLOCKED_COUNT=$((BLOCKED_COUNT + 1)) ;;
    INFRASTRUCTURE_BLOCKED) INFRA_COUNT=$((INFRA_COUNT + 1)) ;;
    UNSUPPORTED) UNSUPPORTED_COUNT=$((UNSUPPORTED_COUNT + 1)) ;;
  esac
}

tail_capture() {
  # Cap captured stdout/stderr to a report-friendly size.
  tail -c 4000 "$1" 2>/dev/null || true
}

# True (exit 0) iff $1 resolves (lexically -- no existence requirement, so this also
# rejects a not-yet-existing path that escapes via `..`) under root $2. Guards against a
# manifest entry's `path` escaping EXAMPLES_ROOT, e.g. `../../etc` or an absolute path
# elsewhere on disk, before it is ever handed to `cp -r`.
path_contained_in_root() {
  local candidate="$1" root="$2"
  python3 -c "
import os, sys
candidate = os.path.normpath(os.path.join(os.getcwd(), sys.argv[1]))
root = os.path.normpath(os.path.join(os.getcwd(), sys.argv[2]))
sys.exit(0 if (candidate == root or candidate.startswith(root + os.sep)) else 1)
" "$candidate" "$root"
}

# ---------------------------------------------------------------------------
# 5. Main loop
# ---------------------------------------------------------------------------
EXCLUDED_FILE="$WORK_ROOT/excluded.jsonl"
: >"$EXCLUDED_FILE"

while IFS= read -r entry; do
  name="$(jq -r '.name' <<<"$entry")"
  rel_path="$(jq -r '.path' <<<"$entry")"
  kind="$(jq -r '.kind' <<<"$entry")"
  kind_known="$(jq -r '.kind_known' <<<"$entry")"
  status_field="$(jq -r '.status_field' <<<"$entry")"
  excluded="$(jq -r '.excluded' <<<"$entry")"
  receipt_workflow="$(jq -r '.receipt_workflow' <<<"$entry")"
  expect_refusal_pattern="$(jq -r '.expect_refusal_pattern' <<<"$entry")"
  cargo_example_name="$(jq -r '.cargo_example_name' <<<"$entry")"

  if [ "$excluded" = "true" ]; then
    EXCLUDED_COUNT=$((EXCLUDED_COUNT + 1))
    jq -nc --arg name "$name" --arg path "$rel_path" --arg status_field "$status_field" \
      '{name:$name, path:$path, status_field:$status_field}' >>"$EXCLUDED_FILE"
    log "SKIP (excluded, status=$status_field): $name"
    continue
  fi

  log "verifying: $name (kind=$kind)"
  entry_started_epoch="$(date +%s)"

  abs_example_dir="$REPO_ROOT/$rel_path"
  # exit_code_json / *_checked / *_ok default to JSON null/false until a step runs them.
  exit_code_json="null"
  stdout_tail=""
  stderr_tail=""
  dry_run_checked="false"
  dry_run_zero_mutation="false"
  digest_before=""
  digest_after=""
  idempotency_checked="false"
  idempotency_ok="false"
  receipt_checked="false"
  receipt_ok="false"
  tmp_dir=""
  final_status=""
  reason=""
  verify_cmd_desc=""

  if [ "$kind_known" != "true" ]; then
    final_status="UNSUPPORTED"
    reason="harness does not implement kind '$kind' (known kinds: generated-project, rust-example)"
    verify_cmd_desc="(none -- unsupported kind)"
    duration_s=$(( $(date +%s) - entry_started_epoch ))
    emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
      "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
      "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
      "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
    log "  -> $final_status: $reason"
    continue
  fi

  if ! path_contained_in_root "$abs_example_dir" "$EXAMPLES_ROOT"; then
    final_status="INFRASTRUCTURE_BLOCKED"
    reason="declared path resolves outside EXAMPLES_ROOT ($EXAMPLES_ROOT): $abs_example_dir"
    verify_cmd_desc="(none -- path escapes EXAMPLES_ROOT)"
    duration_s=$(( $(date +%s) - entry_started_epoch ))
    emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
      "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
      "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
      "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
    log "  -> $final_status: $reason"
    continue
  fi

  if [ ! -d "$abs_example_dir" ]; then
    final_status="INFRASTRUCTURE_BLOCKED"
    reason="declared path does not exist: $abs_example_dir"
    verify_cmd_desc="(none -- path missing)"
    duration_s=$(( $(date +%s) - entry_started_epoch ))
    emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
      "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
      "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
      "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
    log "  -> $final_status: $reason"
    continue
  fi

  if [ "$kind" = "generated-project" ]; then
    if [ ! -f "$abs_example_dir/ggen.toml" ]; then
      final_status="INFRASTRUCTURE_BLOCKED"
      reason="generated-project entry has no ggen.toml at $abs_example_dir/ggen.toml"
      verify_cmd_desc="(none -- ggen.toml missing)"
      duration_s=$(( $(date +%s) - entry_started_epoch ))
      emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
        "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
        "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
        "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
      log "  -> $final_status: $reason"
      continue
    fi

    if [ "$GGEN_BUILD_OK" != "true" ]; then
      final_status="INFRASTRUCTURE_BLOCKED"
      reason="ggen binary failed to build -- see $GGEN_BUILD_LOG"
      verify_cmd_desc="(none -- ggen binary unavailable)"
      duration_s=$(( $(date +%s) - entry_started_epoch ))
      emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
        "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
        "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
        "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
      log "  -> $final_status: $reason"
      continue
    fi

    tmp_dir="$(mktemp -d "$WORK_ROOT/ex-XXXXXX")/proj"
    cp -R "$abs_example_dir" "$tmp_dir"

    verify_cmd_desc="ggen sync run --dry-run"
    dry_run_checked="true"
    digest_before="$(tree_digest "$tmp_dir")"

    dry_stdout="$WORK_ROOT/${name}.dry.stdout"
    dry_stderr="$WORK_ROOT/${name}.dry.stderr"
    (cd "$tmp_dir" && timeout "${STEP_TIMEOUT}s" env "${UNSET_ARGS[@]}" "$GGEN_BIN" sync run --dry-run --format json) \
      >"$dry_stdout" 2>"$dry_stderr"
    dry_exit=$?

    digest_after="$(tree_digest "$tmp_dir")"
    [ "$digest_before" = "$digest_after" ] && dry_run_zero_mutation="true" || dry_run_zero_mutation="false"

    exit_code_json="$dry_exit"
    stdout_tail="$(tail_capture "$dry_stdout")"
    stderr_tail="$(tail_capture "$dry_stderr")"
    combined_output="$stdout_tail
$stderr_tail"

    if [ "$dry_exit" -ne 0 ]; then
      if [ -n "$expect_refusal_pattern" ] && printf '%s' "$combined_output" | grep -Eq -- "$expect_refusal_pattern"; then
        final_status="TYPED_REFUSAL_AS_DESIGNED"
        reason="dry-run exited $dry_exit but matched declared expect_refusal_pattern"
      else
        final_status="BLOCKED"
        reason="dry-run exited $dry_exit (unexpected -- no matching expect_refusal_pattern declared)"
      fi
    elif [ "$dry_run_zero_mutation" != "true" ]; then
      final_status="BLOCKED"
      reason="dry-run exited 0 but mutated the filesystem (digest before=$digest_before after=$digest_after)"
    else
      # Dry-run clean: proceed to the real (non-dry-run) sync + idempotency check.
      verify_cmd_desc="$verify_cmd_desc && ggen sync run"
      real1_stdout="$WORK_ROOT/${name}.real1.stdout"
      real1_stderr="$WORK_ROOT/${name}.real1.stderr"
      (cd "$tmp_dir" && timeout "${STEP_TIMEOUT}s" env "${UNSET_ARGS[@]}" "$GGEN_BIN" sync run --format json) \
        >"$real1_stdout" 2>"$real1_stderr"
      real1_exit=$?
      digest_real1="$(tree_digest_excluding_receipts "$tmp_dir")"

      if [ "$real1_exit" -ne 0 ]; then
        exit_code_json="$real1_exit"
        stdout_tail="$(tail_capture "$real1_stdout")"
        stderr_tail="$(tail_capture "$real1_stderr")"
        final_status="BLOCKED"
        reason="real sync (non-dry-run) exited $real1_exit"
      else
        verify_cmd_desc="$verify_cmd_desc && ggen sync run (again, idempotency check)"
        real2_stdout="$WORK_ROOT/${name}.real2.stdout"
        real2_stderr="$WORK_ROOT/${name}.real2.stderr"
        (cd "$tmp_dir" && timeout "${STEP_TIMEOUT}s" env "${UNSET_ARGS[@]}" "$GGEN_BIN" sync run --format json) \
          >"$real2_stdout" 2>"$real2_stderr"
        real2_exit=$?
        digest_real2="$(tree_digest_excluding_receipts "$tmp_dir")"

        idempotency_checked="true"
        exit_code_json="$real2_exit"
        stdout_tail="$(tail_capture "$real2_stdout")"
        stderr_tail="$(tail_capture "$real2_stderr")"

        if [ "$real2_exit" -ne 0 ]; then
          idempotency_ok="false"
          final_status="BLOCKED"
          reason="second real sync (idempotency check) exited $real2_exit"
        else
          # Two independent idempotency signals: the tool's own self-report
          # (`.written` must be empty on the second run) and an independent
          # filesystem digest comparison. Both must agree the tree is unchanged.
          second_run_written_count="$(jq -r '.written | length' "$real2_stdout" 2>/dev/null || echo "unknown")"
          digests_equal="false"
          [ "$digest_real1" = "$digest_real2" ] && digests_equal="true"

          if [ "$second_run_written_count" = "0" ] && [ "$digests_equal" = "true" ]; then
            idempotency_ok="true"
          else
            idempotency_ok="false"
          fi

          if [ "$idempotency_ok" != "true" ]; then
            final_status="BLOCKED"
            reason="non-idempotent: second real sync reported .written length=$second_run_written_count, digest_equal=$digests_equal"
          elif [ "$receipt_workflow" = "true" ]; then
            verify_cmd_desc="$verify_cmd_desc && ggen receipt verify"
            receipt_checked="true"
            receipt_stdout="$WORK_ROOT/${name}.receipt.stdout"
            receipt_stderr="$WORK_ROOT/${name}.receipt.stderr"
            (cd "$tmp_dir" && timeout "${STEP_TIMEOUT}s" env "${UNSET_ARGS[@]}" "$GGEN_BIN" receipt verify --format json) \
              >"$receipt_stdout" 2>"$receipt_stderr"
            receipt_exit=$?
            receipt_valid="$(jq -r '.valid' "$receipt_stdout" 2>/dev/null || echo "false")"

            if [ "$receipt_exit" -eq 0 ] && [ "$receipt_valid" = "true" ]; then
              receipt_ok="true"
              final_status="PASS"
              reason="dry-run clean; real sync + idempotency OK; receipt verify OK"
            else
              receipt_ok="false"
              final_status="BLOCKED"
              reason="receipt verify failed (exit=$receipt_exit, valid=$receipt_valid)"
              exit_code_json="$receipt_exit"
              stdout_tail="$(tail_capture "$receipt_stdout")"
              stderr_tail="$(tail_capture "$receipt_stderr")"
            fi
          else
            final_status="PASS"
            reason="dry-run clean (zero mutation); real sync + idempotency OK"
          fi
        fi
      fi
    fi

  elif [ "$kind" = "rust-example" ]; then
    cargo_name="${cargo_example_name:-$name}"
    cargo_name="${cargo_name%.rs}"

    if [ "$receipt_workflow" = "true" ]; then
      final_status="INFRASTRUCTURE_BLOCKED"
      reason="receipt_workflow=true declared for a rust-example entry, which has no project directory for 'ggen receipt verify' to run against"
      verify_cmd_desc="cargo build --example $cargo_name"
    else
      verify_cmd_desc="cargo build --example $cargo_name"

      build_stdout="$WORK_ROOT/${name}.build.stdout"
      build_stderr="$WORK_ROOT/${name}.build.stderr"
      (cd "$REPO_ROOT" && timeout "${STEP_TIMEOUT}s" env "${UNSET_ARGS[@]}" cargo build --example "$cargo_name") \
        >"$build_stdout" 2>"$build_stderr"
      build_exit=$?

      exit_code_json="$build_exit"
      stdout_tail="$(tail_capture "$build_stdout")"
      stderr_tail="$(tail_capture "$build_stderr")"
      combined_output="$stdout_tail
$stderr_tail"

      if [ "$build_exit" -eq 0 ]; then
        final_status="PASS"
        reason="cargo build --example $cargo_name succeeded"
      elif [ -n "$expect_refusal_pattern" ] && printf '%s' "$combined_output" | grep -Eq -- "$expect_refusal_pattern"; then
        final_status="TYPED_REFUSAL_AS_DESIGNED"
        reason="cargo build exited $build_exit but matched declared expect_refusal_pattern"
      else
        final_status="BLOCKED"
        reason="cargo build --example $cargo_name exited $build_exit"
      fi
    fi
  fi

  duration_s=$(( $(date +%s) - entry_started_epoch ))
  emit_result "$name" "$rel_path" "$kind" "$final_status" "$reason" "$verify_cmd_desc" \
    "$exit_code_json" "$stdout_tail" "$stderr_tail" "$duration_s" \
    "$dry_run_checked" "$dry_run_zero_mutation" "$digest_before" "$digest_after" \
    "$idempotency_checked" "$idempotency_ok" "$receipt_checked" "$receipt_ok" "$tmp_dir"
  log "  -> $final_status: $reason"
done < <(jq -c '.[]' "$ENTRIES_JSON")

# ---------------------------------------------------------------------------
# 6. Finalize: JSON + Markdown reports
# ---------------------------------------------------------------------------
RUN_FINISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_DURATION_S=$(( $(date +%s) - RUN_STARTED_EPOCH ))

RUN_STARTED_AT="$RUN_STARTED_AT" RUN_FINISHED_AT="$RUN_FINISHED_AT" \
RUN_DURATION_S="$RUN_DURATION_S" MANIFEST="$MANIFEST" \
RESULTS_FILE="$RESULTS_FILE" EXCLUDED_FILE="$EXCLUDED_FILE" \
JSON_REPORT="$JSON_REPORT" MD_REPORT="$MD_REPORT" \
TOTAL_ENTRIES="$TOTAL_ENTRIES" \
python3 - <<'PY'
import json
import os

started = os.environ["RUN_STARTED_AT"]
finished = os.environ["RUN_FINISHED_AT"]
duration_s = int(os.environ["RUN_DURATION_S"])
manifest = os.environ["MANIFEST"]
results_file = os.environ["RESULTS_FILE"]
excluded_file = os.environ["EXCLUDED_FILE"]
json_path = os.environ["JSON_REPORT"]
md_path = os.environ["MD_REPORT"]
total_entries = int(os.environ["TOTAL_ENTRIES"])


def read_jsonl(path):
    items = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    return items


results = read_jsonl(results_file)
excluded = read_jsonl(excluded_file)

statuses = ["PASS", "TYPED_REFUSAL_AS_DESIGNED", "BLOCKED", "INFRASTRUCTURE_BLOCKED", "UNSUPPORTED"]
summary = {s: 0 for s in statuses}
for r in results:
    if r["status"] in summary:
        summary[r["status"]] += 1
summary["total"] = total_entries
summary["excluded"] = len(excluded)
summary["verified"] = len(results)

report = {
    "harness": "verify-examples-v26.7.17.sh",
    "started_at": started,
    "finished_at": finished,
    "duration_seconds": duration_s,
    "manifest": manifest,
    "manifest_found": True,
    "summary": summary,
    "excluded": excluded,
    "results": results,
}

with open(json_path, "w") as f:
    json.dump(report, f, indent=2)
    f.write("\n")

with open(md_path, "w") as f:
    f.write("# Example Verification Report (v26.7.17)\n\n")
    f.write(f"Started: {started}  \nFinished: {finished}  \nDuration: {duration_s}s  \nManifest: `{manifest}`\n\n")
    f.write("## Summary\n\n")
    f.write("| Status | Count |\n|---|---|\n")
    f.write(f"| Total entries in manifest | {summary['total']} |\n")
    f.write(f"| Excluded (ARCHIVED/DOCUMENTATION_ONLY) | {summary['excluded']} |\n")
    f.write(f"| Verified | {summary['verified']} |\n")
    for s in statuses:
        f.write(f"| {s} | {summary[s]} |\n")
    f.write("\n## Per-example results\n\n")
    f.write("| Name | Kind | Status | Reason |\n|---|---|---|---|\n")
    for r in results:
        reason = r["reason"].replace("|", "\\|").replace("\n", " ")
        f.write(f"| {r['name']} | {r['kind']} | {r['status']} | {reason} |\n")
    if excluded:
        f.write("\n## Excluded entries\n\n")
        f.write("| Name | Path | Status field |\n|---|---|---|\n")
        for e in excluded:
            f.write(f"| {e['name']} | {e['path']} | {e['status_field']} |\n")

print(f"wrote {json_path}")
print(f"wrote {md_path}")
print(json.dumps(summary, indent=2))
PY

log "done. JSON report: $JSON_REPORT"
log "done. Markdown report: $MD_REPORT"

# Non-zero exit if anything is BLOCKED/INFRASTRUCTURE_BLOCKED/UNSUPPORTED, so this
# script is usable as a CI gate; PASS and TYPED_REFUSAL_AS_DESIGNED are both "fine".
FAIL_TOTAL=$((BLOCKED_COUNT + INFRA_COUNT + UNSUPPORTED_COUNT))
if [ "$FAIL_TOTAL" -gt 0 ]; then
  warn "$FAIL_TOTAL entries did not pass (BLOCKED=$BLOCKED_COUNT INFRASTRUCTURE_BLOCKED=$INFRA_COUNT UNSUPPORTED=$UNSUPPORTED_COUNT)"
  exit 1
fi

exit 0
