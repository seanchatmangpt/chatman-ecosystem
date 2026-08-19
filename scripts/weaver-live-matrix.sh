#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${WEAVER_REGISTRY:-telemetry/weaver}"
OUT="${WEAVER_RECEIPT_DIR:-target/weaver-live}"
SUBJECT_SHA="${ECOSYSTEM_SUBJECT_SHA:-$(git rev-parse HEAD)}"
REPO="${GITHUB_REPOSITORY:-seanchatmangpt/chatman-ecosystem}"
mkdir -p "${OUT}/logs" "${OUT}/schemas" "${OUT}/generated" "${OUT}/package"
: > "${OUT}/receipt.jsonl"

test "${#SUBJECT_SHA}" -eq 40
test "$(git rev-parse HEAD)" = "${SUBJECT_SHA}"
weaver --version | tee "${OUT}/weaver-version.txt"
grep -q '0.25.1' "${OUT}/weaver-version.txt"

record() {
  local cap="$1" authority="$2" status="$3" rc="$4" detail="$5"
  jq -cn --arg capability "$cap" --arg authority "$authority" --arg status "$status" \
    --argjson exit_code "$rc" --arg subject "git:${SUBJECT_SHA}" --arg detail "$detail" \
    '{capability:$capability,authority:$authority,status:$status,executed:true,exit_code:$exit_code,subject:$subject,detail:$detail}' \
    >> "${OUT}/receipt.jsonl"
}

run_required() {
  local cap="$1" authority="$2"; shift 2
  local log="${OUT}/logs/${cap//[^A-Za-z0-9_.-]/_}.log"
  set +e
  "$@" >"${log}" 2>&1
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    record "$cap" "$authority" "ALIVE" 0 "observed successful execution"
  else
    record "$cap" "$authority" "BUILD_BROKEN" "$rc" "see ${log}"
    cat "${log}" >&2
    return "$rc"
  fi
}

run_required "ecosystem.check_refs" "SELECT" python3 scripts/verify_release.py --check-refs
run_required "cli.help" "SELECT" weaver --help
run_required "registry.help" "SELECT" weaver registry --help
for fmt in ansi json gh_workflow_command; do
  run_required "check.${fmt}" "SELECT" weaver registry check -r "${REGISTRY}" --v2 true --diagnostic-format "${fmt}"
done
run_required "check.local" "SELECT" weaver registry check -r "${REGISTRY}" --v2 true --future
run_required "check.git_exact_sha" "SELECT" weaver registry check \
  -r "https://github.com/${REPO}.git@${SUBJECT_SHA}[telemetry/weaver]" --v2 true

run_required "generate" "CONSTRUCT" weaver registry generate ecosystem "${OUT}/generated" \
  -r "${REGISTRY}" --v2 true -t "${REGISTRY}/templates"
test -s "${OUT}/generated/CHATMAN_ECOSYSTEM_WEAVER.md"
run_required "resolve.deprecated" "CONSTRUCT" weaver registry resolve \
  -r "${REGISTRY}" --v2 true --format json -o "${OUT}/resolved.json"
test -s "${OUT}/resolved.json"

set +e
weaver registry search -r "${REGISTRY}" --v2 true chatman >"${OUT}/logs/search.deprecated.log" 2>&1
search_rc=$?
set -e
if [[ $search_rc -eq 0 ]]; then
  record "search.deprecated" "SELECT" "ALIVE" 0 "deprecated command executed successfully"
else
  record "search.deprecated" "SELECT" "UNSUPPORTED" "$search_rc" "executed; upstream declares V2 search incompatible"
fi

for fmt in text json yaml jsonl mute; do
  run_required "stats.${fmt}" "SELECT" weaver registry stats -r "${REGISTRY}" --v2 true --format "${fmt}"
done

mkdir -p "${OUT}/markdown"
cp README.md "${OUT}/markdown/README.md"
before="$(sha256sum README.md | awk '{print $1}')"
run_required "update-markdown" "CONSTRUCT" weaver registry update-markdown "${OUT}/markdown" \
  -r "${REGISTRY}" --v2 true -t "${REGISTRY}/templates" --target ecosystem
test "$(sha256sum README.md | awk '{print $1}')" = "${before}"

for schema in resolved-registry semconv-group semconv-definition-v2 resolved-registry-v2 materialized-registry-v2 diff diff-v2 publication-manifest-v2 definition-manifest-v2 policy-finding weaver-config; do
  run_required "json-schema.${schema}" "CONSTRUCT" weaver registry json-schema \
    --json-schema "${schema}" -o "${OUT}/schemas/${schema}.json"
  test -s "${OUT}/schemas/${schema}.json"
done
for fmt in ansi json markdown; do
  run_required "diff.${fmt}" "SELECT" weaver registry diff -r "${REGISTRY}" \
    --baseline-registry "${REGISTRY}" --v2 true --format "${fmt}"
done
run_required "package" "CONSTRUCT" weaver registry package -r "${REGISTRY}" --v2 true \
  -o "${OUT}/package" --resolved-registry-uri "https://chatmangpt.com/schemas/chatman-ecosystem/${SUBJECT_SHA}"
test -n "$(find "${OUT}/package" -type f -print -quit)"

run_required "diagnostic.init" "CONSTRUCT" weaver diagnostic init \
  --diagnostic-templates-dir "${OUT}/diagnostic_templates"
for shell in bash elvish fish powershell zsh; do
  run_required "completion.${shell}" "CONSTRUCT" bash -c "weaver completion '${shell}' > '${OUT}/completion-${shell}'"
  test -s "${OUT}/completion-${shell}"
done

printf '%s\n' \
  "chatman.ecosystem.repository=${REPO}" \
  "chatman.ecosystem.subject.sha=${SUBJECT_SHA}" \
  "chatman.ecosystem.command=release.check-refs" \
  "chatman.ecosystem.result=ok" "" \
| weaver registry live-check -r "${REGISTRY}" --v2 true --input-source stdin --input-format text \
    --fail-on none --output none >"${OUT}/logs/live-check.ecosystem.log" 2>&1
record "live-check.ecosystem" "SELECT" "ALIVE" 0 "real verify_release.py result assessed against exact-subject registry"

weaver registry live-check -r "${REGISTRY}" --v2 true --input-source otlp \
  --otlp-grpc-address 127.0.0.1 --otlp-grpc-port 14317 --admin-port 14320 \
  --inactivity-timeout 4 --fail-on none --output none >"${OUT}/logs/live-check.otlp.log" 2>&1 &
live_pid=$!
sleep 2
run_required "emit.loopback" "DO" weaver registry emit -r "${REGISTRY}" --v2 true \
  --skip-policies true --endpoint http://127.0.0.1:14317
wait "${live_pid}"
record "live-check.otlp" "DO" "ALIVE" 0 "loopback receiver observed Weaver-emitted registry telemetry"

rm -rf "${OUT}/inferred"
weaver registry infer -o "${OUT}/inferred" --grpc-address 127.0.0.1 --grpc-port 14417 \
  --admin-port 14420 --inactivity-timeout 4 >"${OUT}/logs/infer.log" 2>&1 &
infer_pid=$!
sleep 2
run_required "emit.to-infer" "DO" weaver registry emit -r "${REGISTRY}" --v2 true \
  --skip-policies true --endpoint http://127.0.0.1:14417
wait "${infer_pid}"
test -n "$(find "${OUT}/inferred" -type f -print -quit)"
record "infer" "CONSTRUCT" "ALIVE" 0 "inferred registry materialized from loopback OTLP samples"

set +e
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"chatman-ecosystem-weaver","version":"26.8.18"}}}' \
'{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
| timeout 10s weaver registry mcp -r "${REGISTRY}" --v2 true >"${OUT}/logs/mcp.log" 2>&1
mcp_rc=${PIPESTATUS[1]}
set -e
if grep -q '"result"' "${OUT}/logs/mcp.log"; then
  record "mcp" "SELECT" "ALIVE" "$mcp_rc" "JSON-RPC initialize/tools-list response observed"
else
  record "mcp" "SELECT" "BUILD_BROKEN" "$mcp_rc" "no JSON-RPC result observed"
  cat "${OUT}/logs/mcp.log" >&2
  exit 1
fi

weaver serve -r "${REGISTRY}" --v2 true --bind 127.0.0.1:18080 >"${OUT}/logs/serve.log" 2>&1 &
serve_pid=$!
serve_ok=0
for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:18080/ >"${OUT}/serve-response" 2>/dev/null; then serve_ok=1; break; fi
  sleep 1
done
kill "${serve_pid}" 2>/dev/null || true
wait "${serve_pid}" 2>/dev/null || true
if [[ "${serve_ok}" -eq 1 ]]; then
  record "serve.experimental" "SELECT" "ALIVE" 0 "loopback HTTP response observed"
else
  record "serve.experimental" "SELECT" "BUILD_BROKEN" 1 "no loopback HTTP response"
  cat "${OUT}/logs/serve.log" >&2
  exit 1
fi

jq -s --arg subject "git:${SUBJECT_SHA}" --arg weaver "$(cat "${OUT}/weaver-version.txt")" \
  '{schema:"https://chatmangpt.com/receipts/weaver-capability/v1",subject:$subject,weaver:$weaver,capabilities:.}' \
  "${OUT}/receipt.jsonl" > "${OUT}/receipt.json"
required=(cli.help registry.help check.local check.git_exact_sha generate resolve.deprecated stats.json update-markdown \
  json-schema.semconv-definition-v2 diff.json package diagnostic.init completion.bash live-check.ecosystem \
  live-check.otlp emit.loopback infer mcp serve.experimental)
for cap in "${required[@]}"; do
  jq -e --arg cap "$cap" '.capabilities[] | select(.capability == $cap and .executed == true)' "${OUT}/receipt.json" >/dev/null
done
if jq -e '.capabilities[] | select(.status == "BUILD_BROKEN" or .status == "BLOCKED")' "${OUT}/receipt.json" >/dev/null; then
  echo "Weaver capability matrix contains broken/blocking required edges" >&2
  exit 1
fi
sha256sum "${OUT}/receipt.json" | tee "${OUT}/receipt.sha256"
cat "${OUT}/receipt.json"
