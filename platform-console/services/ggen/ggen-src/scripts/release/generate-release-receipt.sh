#!/usr/bin/env bash
# generate-release-receipt.sh -- v26.7.17 DoD gate G9 release-receipt generator.
#
# Provenance note: at the time this script was written (2026-07-17) no repo
# document defines a "G9" gate by that name -- it was searched for (grep -rn
# "G9" across *.md/*.ttl/*.json/*.sh, git log --all, docs/releases/v26.7.17/
# which was empty, docs/jira/v26.7.16/*) and not found. The field list below
# implements exactly the field list handed to this script's authoring task:
# git commit, dirty-tree state, Rust toolchain version, Cargo version,
# Cargo.lock digest, the four real publish-target package digests (ggen,
# ggen-config, ggen-graph, ggen-marketplace), installed-binary digest,
# configuration-schema version, test-report digest, clean-install-log digest,
# the canonical `ggen sync` workflow receipt, a receipt-tamper-report
# summary, a known-defect-disposition summary, and overall release standing.
# See docs/releases/v26.7.17/release-receipt.schema.json for the full shape
# this script emits, including field-by-field rationale.
#
# Every evidence artifact this script cannot find is emitted as
# {"status":"pending", ...: null} rather than omitted or guessed -- this
# script is designed to be run once per gate as the release proceeds, not
# only once at the very end.
#
# Usage:
#   generate-release-receipt.sh [options]
#
# Options (all optional; anything not passed is auto-discovered under
# --release-dir, falling back to "pending"/null if nothing is found there):
#   --release-dir DIR            Default: target/ggen-release/v26.7.17
#   --repo-root DIR              Default: git rev-parse --show-toplevel
#   --version STR                Default: 26.7.17
#   --git-ref STR                Default: null (no tag cut yet)
#   --lockfile PATH              Default: <repo-root>/Cargo.lock
#   --package-ggen PATH              .crate file for the `ggen` package
#   --package-ggen-config PATH       .crate file for `ggen-config`
#   --package-ggen-graph PATH        .crate file for `ggen-graph`
#   --package-ggen-marketplace PATH  .crate file for `ggen-marketplace`
#   --installed-binary PATH      Path to a binary produced by this release's
#                                 own clean-install step (NOT auto-discovered
#                                 from an ambient ~/.cargo/bin/ggen or a dev
#                                 target/debug/ggen -- those did not
#                                 necessarily come from this release)
#   --test-report PATH           Test-report file (json/txt/log)
#   --test-report-summary STR    One-line summary to embed verbatim
#   --clean-install-log PATH     Clean-install log file
#   --workflow-receipt PATH      Default: <repo-root>/.ggen-v2/receipt.json
#   --tamper-report PATH         Release-level receipt-tamper report file
#   --tamper-result STR          pending|clean|tamper_detected (default: pending
#                                 if --tamper-report is absent, else "clean")
#   --tamper-summary STR
#   --defect-disposition PATH    Known-defect-disposition file
#   --defect-open-count N
#   --defect-accepted-risk-count N
#   --defect-summary STR
#   --output PATH                Default: <release-dir>/reports/release-receipt.json
#   -h, --help
#
# Requires: git, rustc, cargo, jq, shasum or sha256sum, date, python3
# (python3 is used only for optional schema validation, see --validate).

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_PATH="${BASH_SOURCE[0]}"
REPO_ROOT="$(git -C "$(dirname "$SCRIPT_PATH")" rev-parse --show-toplevel 2>/dev/null || pwd)"
RELEASE_VERSION="26.7.17"
GIT_REF=""
RELEASE_DIR="${REPO_ROOT}/target/ggen-release/v26.7.17"
LOCKFILE=""
PKG_GGEN=""
PKG_GGEN_CONFIG=""
PKG_GGEN_GRAPH=""
PKG_GGEN_MARKETPLACE=""
INSTALLED_BINARY=""
TEST_REPORT=""
TEST_REPORT_SUMMARY=""
CLEAN_INSTALL_LOG=""
WORKFLOW_RECEIPT=""
TAMPER_REPORT=""
TAMPER_RESULT=""
TAMPER_SUMMARY=""
DEFECT_DISPOSITION=""
DEFECT_OPEN_COUNT=""
DEFECT_ACCEPTED_RISK_COUNT=""
DEFECT_SUMMARY=""
OUTPUT=""
DO_VALIDATE=0
INVOCATION="$0 $*"

usage() { sed -n '2,60p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --release-dir) RELEASE_DIR="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --version) RELEASE_VERSION="$2"; shift 2 ;;
    --git-ref) GIT_REF="$2"; shift 2 ;;
    --lockfile) LOCKFILE="$2"; shift 2 ;;
    --package-ggen) PKG_GGEN="$2"; shift 2 ;;
    --package-ggen-config) PKG_GGEN_CONFIG="$2"; shift 2 ;;
    --package-ggen-graph) PKG_GGEN_GRAPH="$2"; shift 2 ;;
    --package-ggen-marketplace) PKG_GGEN_MARKETPLACE="$2"; shift 2 ;;
    --installed-binary) INSTALLED_BINARY="$2"; shift 2 ;;
    --test-report) TEST_REPORT="$2"; shift 2 ;;
    --test-report-summary) TEST_REPORT_SUMMARY="$2"; shift 2 ;;
    --clean-install-log) CLEAN_INSTALL_LOG="$2"; shift 2 ;;
    --workflow-receipt) WORKFLOW_RECEIPT="$2"; shift 2 ;;
    --tamper-report) TAMPER_REPORT="$2"; shift 2 ;;
    --tamper-result) TAMPER_RESULT="$2"; shift 2 ;;
    --tamper-summary) TAMPER_SUMMARY="$2"; shift 2 ;;
    --defect-disposition) DEFECT_DISPOSITION="$2"; shift 2 ;;
    --defect-open-count) DEFECT_OPEN_COUNT="$2"; shift 2 ;;
    --defect-accepted-risk-count) DEFECT_ACCEPTED_RISK_COUNT="$2"; shift 2 ;;
    --defect-summary) DEFECT_SUMMARY="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --validate) DO_VALIDATE=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -z "$LOCKFILE" ]] && LOCKFILE="${REPO_ROOT}/Cargo.lock"
[[ -z "$WORKFLOW_RECEIPT" ]] && WORKFLOW_RECEIPT="${REPO_ROOT}/.ggen-v2/receipt.json"
[[ -z "$OUTPUT" ]] && OUTPUT="${RELEASE_DIR}/reports/release-receipt.json"

for cmd in git rustc cargo jq date; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "required command not found: $cmd" >&2; exit 1; }
done

if command -v shasum >/dev/null 2>&1; then
  sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }
  sha256_stdin() { shasum -a 256 | awk '{print $1}'; }
elif command -v sha256sum >/dev/null 2>&1; then
  sha256_file() { sha256sum "$1" | awk '{print $1}'; }
  sha256_stdin() { sha256sum | awk '{print $1}'; }
else
  echo "neither shasum nor sha256sum found" >&2
  exit 1
fi

# Auto-discover convention under --release-dir: packages/<crate>-*.crate,
# logs/test-report*, logs/clean-install*, reports/*tamper*,
# reports/*defect*. install-roots/** is deliberately NOT auto-globbed for
# --installed-binary (see the option's own doc comment above): a wrong glob
# match there would silently bind an unrelated binary's digest to this
# release, which is worse than leaving the field "pending".
discover_one() {
  local dir="$1" pattern="$2"
  local match
  match="$(find "$dir" -type f -name "$pattern" 2>/dev/null | sort | head -n1 || true)"
  [[ -n "$match" ]] && printf '%s' "$match"
}

[[ -z "$PKG_GGEN" ]] && PKG_GGEN="$(discover_one "${RELEASE_DIR}/packages" 'ggen-[0-9]*.crate' || true)"
[[ -z "$PKG_GGEN_CONFIG" ]] && PKG_GGEN_CONFIG="$(discover_one "${RELEASE_DIR}/packages" 'ggen-config-*.crate' || true)"
[[ -z "$PKG_GGEN_GRAPH" ]] && PKG_GGEN_GRAPH="$(discover_one "${RELEASE_DIR}/packages" 'ggen-graph-*.crate' || true)"
[[ -z "$PKG_GGEN_MARKETPLACE" ]] && PKG_GGEN_MARKETPLACE="$(discover_one "${RELEASE_DIR}/packages" 'ggen-marketplace-*.crate' || true)"
[[ -z "$TEST_REPORT" ]] && TEST_REPORT="$(discover_one "${RELEASE_DIR}/logs" 'test-report*' || true)"
[[ -z "$CLEAN_INSTALL_LOG" ]] && CLEAN_INSTALL_LOG="$(discover_one "${RELEASE_DIR}/logs" 'clean-install*' || true)"
[[ -z "$TAMPER_REPORT" ]] && TAMPER_REPORT="$(discover_one "${RELEASE_DIR}/reports" '*tamper*' || true)"
[[ -z "$DEFECT_DISPOSITION" ]] && DEFECT_DISPOSITION="$(discover_one "${RELEASE_DIR}/reports" '*defect*' || true)"

# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------
GIT_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD)"
GIT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
GIT_PORCELAIN="$(git -C "$REPO_ROOT" status --porcelain)"
if [[ -n "$GIT_PORCELAIN" ]]; then
  GIT_DIRTY=true
  GIT_DIRTY_COUNT="$(printf '%s\n' "$GIT_PORCELAIN" | grep -c .)"
  GIT_DIRTY_SHA256="$(printf '%s\n' "$GIT_PORCELAIN" | sha256_stdin)"
else
  GIT_DIRTY=false
  GIT_DIRTY_COUNT=0
  GIT_DIRTY_SHA256="null"
fi

# ---------------------------------------------------------------------------
# toolchain
# ---------------------------------------------------------------------------
RUSTC_VERBOSE="$(rustc --version --verbose)"
RUSTC_VERSION="$(rustc --version | awk '{print $2}')"
RUSTC_COMMIT_HASH="$(printf '%s\n' "$RUSTC_VERBOSE" | awk -F': ' '/^commit-hash:/{print $2}')"
RUSTC_HOST="$(printf '%s\n' "$RUSTC_VERBOSE" | awk -F': ' '/^host:/{print $2}')"
CARGO_VERSION="$(cargo --version | awk '{print $2}')"
TOOLCHAIN_PIN=""
if [[ -f "${REPO_ROOT}/rust-toolchain.toml" ]]; then
  TOOLCHAIN_PIN="$(awk -F'"' '/^channel/{print $2}' "${REPO_ROOT}/rust-toolchain.toml")"
fi

# ---------------------------------------------------------------------------
# lockfile
# ---------------------------------------------------------------------------
if [[ -f "$LOCKFILE" ]]; then
  LOCKFILE_PRESENT=true
  LOCKFILE_SHA256="$(sha256_file "$LOCKFILE")"
else
  LOCKFILE_PRESENT=false
  LOCKFILE_SHA256="null"
fi

# ---------------------------------------------------------------------------
# packages (the 4 real publish targets)
# ---------------------------------------------------------------------------
package_json() {
  local name="$1" path="$2"
  if [[ -n "$path" && -f "$path" ]]; then
    local sha ver
    sha="$(sha256_file "$path")"
    ver="$(basename "$path" .crate | sed -E "s/^${name}-//")"
    jq -n --arg n "$name" --arg p "$path" --arg s "$sha" --arg v "$ver" \
      '{crate_name:$n, status:"packaged", version:$v, crate_file_path:$p, sha256:$s}'
  else
    jq -n --arg n "$name" \
      '{crate_name:$n, status:"pending", version:null, crate_file_path:null, sha256:null}'
  fi
}

PACKAGES_JSON="$(jq -s '.' \
  <(package_json "ggen" "$PKG_GGEN") \
  <(package_json "ggen-config" "$PKG_GGEN_CONFIG") \
  <(package_json "ggen-graph" "$PKG_GGEN_GRAPH") \
  <(package_json "ggen-marketplace" "$PKG_GGEN_MARKETPLACE"))"

# ---------------------------------------------------------------------------
# installed binary
# ---------------------------------------------------------------------------
if [[ -n "$INSTALLED_BINARY" && -f "$INSTALLED_BINARY" ]]; then
  INSTALLED_BINARY_STATUS="present"
  INSTALLED_BINARY_SHA256="$(sha256_file "$INSTALLED_BINARY")"
  INSTALLED_BINARY_VERSION_OUTPUT="$("$INSTALLED_BINARY" --version 2>&1 || true)"
else
  INSTALLED_BINARY_STATUS="pending"
  INSTALLED_BINARY_SHA256="null"
  INSTALLED_BINARY_VERSION_OUTPUT="null"
fi

# ---------------------------------------------------------------------------
# configuration schema version (ggen-config's own package version -- see
# schema $defs.configuration_schema for why this proxy is used)
# ---------------------------------------------------------------------------
CONFIG_CRATE_VERSION="null"
if PKGID="$(cargo pkgid -p ggen-config --manifest-path "${REPO_ROOT}/Cargo.toml" 2>/dev/null)"; then
  CONFIG_CRATE_VERSION="$(printf '%s' "$PKGID" | sed -E 's/.*#//')"
fi
CONFIG_NOTE="ggen.toml has two independently-defined, incompatible schemas at v26.7.17 (see .claude/rules/architecture.md's 'ggen.toml has two schemas' section). This field binds only the ggen-config-owned declarative-rules schema (GgenManifest), using ggen-config's own crate version as a proxy: no independent numeric schema-version constant exists in ggen-config as of 2026-07-17."

# ---------------------------------------------------------------------------
# test report / clean install log (generic evidence artifacts)
# ---------------------------------------------------------------------------
evidence_json() {
  local path="$1" present_status="$2"
  if [[ -n "$path" && -f "$path" ]]; then
    jq -n --arg p "$path" --arg s "$(sha256_file "$path")" --arg st "$present_status" \
      '{status:$st, path:$p, sha256:$s}'
  else
    jq -n '{status:"pending", path:null, sha256:null}'
  fi
}

evidence_with_summary_json() {
  local path="$1" summary="$2" present_status="$3"
  if [[ -n "$path" && -f "$path" ]]; then
    if [[ -n "$summary" ]]; then
      jq -n --arg p "$path" --arg s "$(sha256_file "$path")" --arg st "$present_status" --arg sm "$summary" \
        '{status:$st, path:$p, sha256:$s, summary:$sm}'
    else
      jq -n --arg p "$path" --arg s "$(sha256_file "$path")" --arg st "$present_status" \
        '{status:$st, path:$p, sha256:$s, summary:null}'
    fi
  else
    if [[ -n "$summary" ]]; then
      jq -n --arg sm "$summary" '{status:"pending", path:null, sha256:null, summary:$sm}'
    else
      jq -n '{status:"pending", path:null, sha256:null, summary:null}'
    fi
  fi
}

TEST_REPORT_JSON="$(evidence_with_summary_json "$TEST_REPORT" "$TEST_REPORT_SUMMARY" "present")"
CLEAN_INSTALL_LOG_JSON="$(evidence_json "$CLEAN_INSTALL_LOG" "present")"

# ---------------------------------------------------------------------------
# canonical workflow receipt (.ggen-v2/receipt.json)
# ---------------------------------------------------------------------------
if [[ -f "$WORKFLOW_RECEIPT" ]]; then
  WF_SHA256="$(sha256_file "$WORKFLOW_RECEIPT")"
  WF_CHAIN_HASH="$(jq -r '.chain_hash_hex // empty' "$WORKFLOW_RECEIPT" 2>/dev/null || true)"
  WF_VERSION="$(jq -r '.version // empty' "$WORKFLOW_RECEIPT" 2>/dev/null || true)"
  WF_SIGNATURE="$(jq -r '.signature_hex // empty' "$WORKFLOW_RECEIPT" 2>/dev/null || true)"
  if [[ -n "$WF_SIGNATURE" ]]; then WF_SIGNED=true; else WF_SIGNED=false; fi

  if [[ -z "$WF_CHAIN_HASH" ]]; then
    WF_CHAIN_HASH_JSON="null"
  else
    WF_CHAIN_HASH_JSON="$(jq -n --arg v "$WF_CHAIN_HASH" '$v')"
  fi
  if [[ -z "$WF_VERSION" ]]; then
    WF_VERSION_JSON="null"
  else
    WF_VERSION_JSON="$(jq -n --arg v "$WF_VERSION" '($v|tonumber)')"
  fi

  WORKFLOW_RECEIPT_JSON="$(jq -n \
    --arg p "$WORKFLOW_RECEIPT" --arg s "$WF_SHA256" \
    --argjson ch "$WF_CHAIN_HASH_JSON" \
    --argjson signed "$WF_SIGNED" \
    --argjson ver "$WF_VERSION_JSON" \
    '{status:"present", path:$p, sha256:$s, chain_hash_hex:$ch, signed:$signed, receipt_record_version:$ver}')"
else
  WORKFLOW_RECEIPT_JSON="$(jq -n --arg p "$WORKFLOW_RECEIPT" \
    '{status:"pending", path:$p, sha256:null, chain_hash_hex:null, signed:null, receipt_record_version:null}')"
fi

# ---------------------------------------------------------------------------
# receipt-tamper report
# ---------------------------------------------------------------------------
if [[ -n "$TAMPER_REPORT" && -f "$TAMPER_REPORT" ]]; then
  [[ -z "$TAMPER_RESULT" ]] && TAMPER_RESULT="clean"
  TAMPER_JSON="$(jq -n --arg p "$TAMPER_REPORT" --arg s "$(sha256_file "$TAMPER_REPORT")" \
    --arg r "$TAMPER_RESULT" --arg sm "${TAMPER_SUMMARY:-}" \
    '{status:"present", path:$p, sha256:$s, result:$r, summary:(if $sm=="" then null else $sm end)}')"
else
  [[ -z "$TAMPER_RESULT" ]] && TAMPER_RESULT="pending"
  TAMPER_JSON="$(jq -n --arg r "$TAMPER_RESULT" --arg sm "${TAMPER_SUMMARY:-}" \
    '{status:"pending", path:null, sha256:null, result:$r, summary:(if $sm=="" then null else $sm end)}')"
fi

# ---------------------------------------------------------------------------
# known-defect disposition
# ---------------------------------------------------------------------------
if [[ -n "$DEFECT_DISPOSITION" && -f "$DEFECT_DISPOSITION" ]]; then
  DEFECT_JSON="$(jq -n --arg p "$DEFECT_DISPOSITION" --arg s "$(sha256_file "$DEFECT_DISPOSITION")" \
    --arg oc "${DEFECT_OPEN_COUNT:-}" --arg arc "${DEFECT_ACCEPTED_RISK_COUNT:-}" --arg sm "${DEFECT_SUMMARY:-}" \
    '{status:"present", path:$p, sha256:$s,
      open_count:(if $oc=="" then null else ($oc|tonumber) end),
      accepted_risk_count:(if $arc=="" then null else ($arc|tonumber) end),
      summary:(if $sm=="" then null else $sm end)}')"
else
  DEFECT_JSON="$(jq -n --arg oc "${DEFECT_OPEN_COUNT:-}" --arg arc "${DEFECT_ACCEPTED_RISK_COUNT:-}" --arg sm "${DEFECT_SUMMARY:-}" \
    '{status:"pending", path:null, sha256:null,
      open_count:(if $oc=="" then null else ($oc|tonumber) end),
      accepted_risk_count:(if $arc=="" then null else ($arc|tonumber) end),
      summary:(if $sm=="" then null else $sm end)}')"
fi

# ---------------------------------------------------------------------------
# assemble + compute standing
# ---------------------------------------------------------------------------
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SCRIPT_REL="$(python3 -c "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$SCRIPT_PATH" "$REPO_ROOT" 2>/dev/null || echo "$SCRIPT_PATH")"

RECEIPT_JSON="$(jq -n \
  --argjson schema_version 1 \
  --arg release_version "$RELEASE_VERSION" \
  --arg git_ref "${GIT_REF:-}" \
  --arg generated_at "$GENERATED_AT" \
  --arg gen_script "$SCRIPT_REL" \
  --arg gen_invocation "$INVOCATION" \
  --arg git_commit "$GIT_COMMIT" \
  --arg git_branch "$GIT_BRANCH" \
  --argjson git_dirty "$GIT_DIRTY" \
  --argjson git_dirty_count "$GIT_DIRTY_COUNT" \
  --arg git_dirty_sha256 "$GIT_DIRTY_SHA256" \
  --arg rustc_version "$RUSTC_VERSION" \
  --arg rustc_commit_hash "${RUSTC_COMMIT_HASH:-}" \
  --arg rustc_host "${RUSTC_HOST:-}" \
  --arg cargo_version "$CARGO_VERSION" \
  --arg toolchain_pin "${TOOLCHAIN_PIN:-}" \
  --arg lockfile_path "$LOCKFILE" \
  --argjson lockfile_present "$LOCKFILE_PRESENT" \
  --arg lockfile_sha256 "$LOCKFILE_SHA256" \
  --argjson packages "$PACKAGES_JSON" \
  --arg ib_status "$INSTALLED_BINARY_STATUS" \
  --arg ib_path "${INSTALLED_BINARY:-}" \
  --arg ib_sha256 "$INSTALLED_BINARY_SHA256" \
  --arg ib_version_output "$INSTALLED_BINARY_VERSION_OUTPUT" \
  --arg config_crate_version "$CONFIG_CRATE_VERSION" \
  --arg config_note "$CONFIG_NOTE" \
  --argjson test_report "$TEST_REPORT_JSON" \
  --argjson clean_install_log "$CLEAN_INSTALL_LOG_JSON" \
  --argjson workflow_receipt "$WORKFLOW_RECEIPT_JSON" \
  --argjson tamper "$TAMPER_JSON" \
  --argjson defect "$DEFECT_JSON" \
  '
  {
    schema_version: $schema_version,
    release: { version: $release_version, git_ref: (if $git_ref == "" then null else $git_ref end) },
    generated_at_utc: $generated_at,
    generator: { script: $gen_script, invocation: $gen_invocation },
    git: {
      commit_sha: $git_commit,
      branch: $git_branch,
      dirty: $git_dirty,
      dirty_file_count: $git_dirty_count,
      dirty_status_sha256: (if $git_dirty_sha256 == "null" then null else $git_dirty_sha256 end)
    },
    toolchain: {
      rustc_version: $rustc_version,
      rustc_commit_hash: (if $rustc_commit_hash == "" then null else $rustc_commit_hash end),
      rustc_host: (if $rustc_host == "" then null else $rustc_host end),
      cargo_version: $cargo_version,
      toolchain_pin: (if $toolchain_pin == "" then null else $toolchain_pin end)
    },
    lockfile: {
      path: $lockfile_path,
      present: $lockfile_present,
      sha256: (if $lockfile_sha256 == "null" then null else $lockfile_sha256 end)
    },
    packages: $packages,
    installed_binary: {
      status: $ib_status,
      path: (if $ib_path == "" then null else $ib_path end),
      sha256: (if $ib_sha256 == "null" then null else $ib_sha256 end),
      version_output: (if $ib_version_output == "null" or $ib_version_output == "" then null else $ib_version_output end)
    },
    configuration_schema: {
      defining_crate: "ggen-config",
      crate_version: (if $config_crate_version == "null" then null else $config_crate_version end),
      note: $config_note
    },
    test_report: $test_report,
    clean_install_log: $clean_install_log,
    workflow_receipt: $workflow_receipt,
    receipt_tamper_report: $tamper,
    known_defect_disposition: $defect
  }
  ')"

# standing computation
BLOCKING="$(jq -n --argjson r "$RECEIPT_JSON" '
  [
    (if ([$r.packages[] | select(.status=="pending")] | length) > 0 then "packages" else empty end),
    (if $r.installed_binary.status=="pending" then "installed_binary" else empty end),
    (if $r.test_report.status=="pending" then "test_report" else empty end),
    (if $r.clean_install_log.status=="pending" then "clean_install_log" else empty end),
    (if $r.workflow_receipt.status=="pending" then "workflow_receipt" else empty end),
    (if $r.receipt_tamper_report.status=="pending" then "receipt_tamper_report" else empty end),
    (if $r.known_defect_disposition.status=="pending" then "known_defect_disposition" else empty end)
  ]
')"

STANDING_STATUS="PENDING"
STANDING_REASON="One or more required evidence artifacts have not been produced yet."
if [[ "$(printf '%s' "$BLOCKING" | jq 'length')" -eq 0 ]]; then
  if [[ "$(printf '%s' "$RECEIPT_JSON" | jq -r '.receipt_tamper_report.result')" == "tamper_detected" ]]; then
    STANDING_STATUS="RED"
    STANDING_REASON="Receipt-tamper report reported tamper_detected."
  elif [[ "$GIT_DIRTY" == "true" ]]; then
    STANDING_STATUS="AMBER"
    STANDING_REASON="All evidence artifacts present, but the working tree was dirty (${GIT_DIRTY_COUNT} entries) at generation time."
  elif [[ "$(printf '%s' "$RECEIPT_JSON" | jq -r '.known_defect_disposition.open_count // 0')" != "0" ]]; then
    STANDING_STATUS="AMBER"
    STANDING_REASON="All evidence artifacts present and tree was clean, but known open defects remain (see known_defect_disposition)."
  else
    STANDING_STATUS="GREEN"
    STANDING_REASON="All evidence artifacts present, tree clean, no tamper detected, no open defects."
  fi
fi

RECEIPT_JSON="$(jq -n --argjson r "$RECEIPT_JSON" --arg st "$STANDING_STATUS" --arg reason "$STANDING_REASON" --argjson blocking "$BLOCKING" \
  '$r + {standing: {status:$st, reason:$reason, blocking:$blocking}}')"

mkdir -p "$(dirname "$OUTPUT")"
printf '%s\n' "$RECEIPT_JSON" | jq '.' > "$OUTPUT"

echo "release receipt written: $OUTPUT" >&2

if [[ "$DO_VALIDATE" -eq 1 ]]; then
  SCHEMA="${REPO_ROOT}/docs/releases/v26.7.17/release-receipt.schema.json"
  if command -v python3 >/dev/null 2>&1 && python3 -c "import jsonschema" >/dev/null 2>&1; then
    python3 -c "
import json, sys
from jsonschema import Draft202012Validator
schema = json.load(open('$SCHEMA'))
instance = json.load(open('$OUTPUT'))
v = Draft202012Validator(schema)
errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
if errors:
    for e in errors:
        print(f'SCHEMA VIOLATION at {list(e.path)}: {e.message}', file=sys.stderr)
    sys.exit(1)
print('release receipt is schema-valid')
"
  else
    echo "--validate requested but python3+jsonschema not available; skipping" >&2
  fi
fi
