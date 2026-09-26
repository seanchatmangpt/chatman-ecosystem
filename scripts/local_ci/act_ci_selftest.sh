#!/usr/bin/env bash
# act_ci_selftest.sh — falsifier harness for act_ci.sh's classifier (v26.9.26, lane W4-F).
# Extracts the single definition of act_ci_classify() from the real act_ci.sh (no test/prod
# drift) and runs synthetic-log fixtures against it. Exit 0 iff every fixture classifies
# as expected; any mismatch exits 1. This script never weakens act_ci.sh.
# usage: act_ci_selftest.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ACT_CI="$HERE/act_ci.sh"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# extract exactly the classifier function from the real script
sed -n '/^act_ci_classify()/,/^}/p' "$ACT_CI" > "$TMP/cls.sh"
grep -q '^act_ci_classify()' "$TMP/cls.sh" || { echo "SELFTEST BROKEN: classifier not extracted from $ACT_CI"; exit 2; }
# shellcheck source=/dev/null
. "$TMP/cls.sh"

expect() { # expect <want> <rc> <logfile> <label>
  local want=$1 rc=$2 log=$3 label=$4 got
  got=$(act_ci_classify "$rc" "$log")
  if [ "$got" = "$want" ]; then
    echo "PASS  $label -> $got"
  else
    echo "FAIL  $label -> got [$got] want [$want]"
    exit 1
  fi
}

# (a) transport storm: colima/containerd I/O error, rc!=0 — must be BLOCKED(TRANSPORT), not FAIL
printf 'time="2026-09-26T12:00:00Z" level=fatal msg="Unable to read from socket: input/output error"\n[deploy-test/lint] ❌  Error: exit code 1\n' > "$TMP/a.log"
expect 'BLOCKED(TRANSPORT_FAILURE:act-runtime)' 1 "$TMP/a.log" "a: input/output error storm"

# (a2) second new pattern: image-exists probe failure (containerd storm), rc=125
printf '[deploy-test/lint] failed to fetch OAuth token: unexpected status code: unable to determine if image already exists ("catthehacker/ubuntu:act-24.04")\n' > "$TMP/a2.log"
expect 'BLOCKED(TRANSPORT_FAILURE:act-runtime)' 125 "$TMP/a2.log" "a2: unable-to-determine-image-exists storm"

# (b) rc=0 but schedule-gated no-op: zero jobs executed — must refuse PASS
printf '⭐ Run main\n[validate] no jobs matched event push — nothing to do\n[validate] skipping: schedule gate not met\n' > "$TMP/b.log"
expect 'FAIL(zero_jobs_ran)' 0 "$TMP/b.log" "b: rc=0 zero jobs"

# (c) normal successful run: job started and succeeded — PASS
printf '[deploy-test/lint] 🚀  Start image=catthehacker/ubuntu:act-24.04\n[deploy-test/lint] ⭐ Run set -euo pipefail\n[deploy-test/lint] ✅  Success -- main -- Set up job\n' > "$TMP/c.log"
expect 'PASS' 0 "$TMP/c.log" "c: normal success"

# (r1) regression: pre-existing transport pattern still BLOCKED
printf 'Cannot connect to the Docker daemon at unix:///Users/sac/.colima/default/docker.sock\n' > "$TMP/r1.log"
expect 'BLOCKED(TRANSPORT_FAILURE:act-runtime)' 1 "$TMP/r1.log" "r1: daemon down (pre-existing pattern)"

# (r2) regression: genuine failure with no transport signature stays FAIL
printf '[deploy-test/lint] ⭐ Run mix test\n[deploy-test/lint]   3 failures\n[deploy-test/lint] ❌  Failure - Main mix test\nError: Process completed with exit code 1.\n' > "$TMP/r2.log"
expect 'FAIL' 1 "$TMP/r2.log" "r2: real test failure stays FAIL"

# (r3) regression: rc=0 with jobs still PASS after classifier restructure
printf '[other] 🚀  Start image=catthehacker/ubuntu:act-24.04\n[other] ✅  Success\n' > "$TMP/r3.log"
expect 'PASS' 0 "$TMP/r3.log" "r3: rc=0 with job start stays PASS"

# anti-vacuity: strip job-start markers from (c) — the classifier MUST flip to refusal,
# proving fix B has a witnessed firing (revert-mutation must change the verdict)
grep -v '🚀  Start image=' "$TMP/c.log" > "$TMP/c-stripped.log"
expect 'FAIL(zero_jobs_ran)' 0 "$TMP/c-stripped.log" "anti-vacuity: (c) minus job markers flips to FAIL(zero_jobs_ran)"

echo "ALL FIXTURES PASS"
