#!/usr/bin/env bash
# act-ci.sh — run a repo's GitHub workflow locally with act on the colima "default" VM,
# against an EXACT commit, and write a receipt. Local CI replaces GitHub Actions (operator 2026-09-25).
#
# usage: act-ci.sh <repo-name> <sha> <workflow-file> [event] [job]
#   repo-name: directory under /Users/sac (canonical checkout; read-only use)
#   event:     push (default) | pull_request | workflow_dispatch
# Sandbox: ephemeral single-commit git repo under $SANDBOX_ROOT (authority NONE), removed after the run.
set -euo pipefail
REPO=$1; SHA=$2; WF=$3; EVENT=${4:-push}; JOB=${5:-}
S=${ACT_CI_ROOT:?set ACT_CI_ROOT to a scratch dir}
SANDBOX_ROOT=$S/act/sandbox; RECEIPTS=$S/act/receipts; LOCK=$S/act/.lock
export DOCKER_HOST=${ACT_CI_DOCKER_HOST:-unix://$HOME/.colima/default/docker.sock}
mkdir -p "$SANDBOX_ROOT" "$RECEIPTS"
CANON=${ACT_CI_CANON_ROOT:-$HOME}/$REPO
FULL=$(git -C "$CANON" rev-parse --verify "$SHA^{commit}")
BOX=$SANDBOX_ROOT/$REPO-${FULL:0:12}-$$
LOG=$RECEIPTS/$REPO-${FULL:0:12}-$(basename "$WF" .yml)${JOB:+-$JOB}.log
# one act run at a time: the default colima VM is 2 CPU / 4 GiB
exec 9>"$LOCK"; flock 9 2>/dev/null || { while ! mkdir "$LOCK.d" 2>/dev/null; do sleep 5; done; trap 'rmdir "$LOCK.d"' EXIT; }
mkdir -p "$BOX"
git -C "$BOX" init -q
git -C "$BOX" remote add origin "https://github.com/${ACT_CI_OWNER:-seanchatmangpt}/$REPO"
git -C "$BOX" fetch -q --no-tags "$CANON" "$FULL"
git -C "$BOX" -c advice.detachedHead=false checkout -q "$FULL"
test "$(git -C "$BOX" rev-parse HEAD)" = "$FULL"
EV=$BOX/.act-event.json
case "$EVENT" in
  pull_request) printf '{"pull_request":{"head":{"sha":"%s"},"number":0}}' "$FULL" >"$EV" ;;
  *) printf '{"after":"%s","ref":"refs/heads/main"}' "$FULL" >"$EV" ;;
esac
set +e
( cd "$BOX" && act "$EVENT" -W ".github/workflows/$WF" ${JOB:+-j "$JOB"} -e "$EV" \
    -P ubuntu-latest=catthehacker/ubuntu:act-24.04 -P ubuntu-24.04=catthehacker/ubuntu:act-24.04 \
    -P ubuntu-22.04=catthehacker/ubuntu:act-24.04 --pull=false --rm --container-daemon-socket - \
    --artifact-server-path "$S/act/artifacts/$REPO-${FULL:0:12}" \
    -s GITHUB_TOKEN="$(gh auth token)" --env GITHUB_SHA="$FULL" ) >"$LOG" 2>&1
RC=$?
set -e
rm -rf "$BOX"
LOGD=$(shasum -a 256 "$LOG" | cut -d' ' -f1)
WFD=$(git -C "$CANON" show "$FULL:.github/workflows/$WF" | shasum -a 256 | cut -d' ' -f1)
# classify (v26.9.26 classifier fixes, lane W4-F):
#   fix A — colima/containerd transport storms ("input/output error",
#           "unable to determine if image already exists") are BLOCKED(TRANSPORT), not FAIL;
#   fix B — rc=0 with zero executed jobs (act logs "[job] 🚀  Start image=..." per job start)
#           is FAIL(zero_jobs_ran): a PASS requires >=1 executed job.
act_ci_classify() {
  local rc=$1 log=$2
  if [ "$rc" -eq 0 ]; then
    if grep -qE '\] 🚀 +Start image=' "$log"; then
      printf 'PASS'
    else
      printf 'FAIL(zero_jobs_ran)'
    fi
  elif grep -qE 'failed to start container|Cannot connect to the Docker daemon|image .* not found|no such image|manifest unknown|input/output error|unable to determine if image already exists' "$log"; then
    printf 'BLOCKED(TRANSPORT_FAILURE:act-runtime)'
  else
    printf 'FAIL'
  fi
}
STANDING=$(act_ci_classify "$RC" "$LOG")
cat >"${LOG%.log}.receipt.json" <<JSON
{"schema":"v26.9.25/act-ci-receipt/1","repository":"seanchatmangpt/$REPO","subject_sha":"$FULL",
 "workflow":".github/workflows/$WF","workflow_sha256":"sha256:$WFD","event":"$EVENT","job":"${JOB}",
 "runner":"act $(act --version | awk '{print $3}') on colima default (DOCKER_HOST=$DOCKER_HOST)",
 "exit_code":$RC,"result":"$STANDING","log":"$LOG","log_sha256":"sha256:$LOGD",
 "evidence_ceiling":"LOCAL_ACT_RUN","authority":"NONE"}
JSON
echo "$STANDING rc=$RC receipt=${LOG%.log}.receipt.json"
exit $RC
