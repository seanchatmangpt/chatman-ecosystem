#!/bin/sh
# R2-X-HOSTSKIP gate (xaas). usage: r2-x-hostskip.sh [subject-worktree]
# Clause 0: wave prefix under the xaas .tool-versions pin (format + compile --force --warnings-as-errors).
# Clause 1 (host: asdf pins under HOME, python3 with rdflib, the ggen_igniter int checkout present): the three
#   host-coupled real courts RUN and pass; 0 failures and 0 skipped (a guard may not skip where its precondition
#   holds -- this is the in-gate anti-vacuity check).
# Clause 2 (hosted-runner shape: fresh HOME so ~/.asdf/... is absent; python3 with no site-packages so
#   `import rdflib` fails; GGEN_IGNITER_DIR pointing at an absent checkout, as on the runner): the same files
#   report 0 failures; the guarded courts (court_receipt REAL mix format court, semantic_receipt REAL
#   ggen-igniter-format court, successor_law.py) are among the named skips (>= 3 skipped).
# Witnessed without the guards (CI runs 35922997741 @246460c, 35924767606 @295e020): clause 2 fails
#   court_receipt_test.exs:306, semantic_receipt_test.exs:196 and successor_test.exs:135.
set -eu
SUBJ=$(cd "${1:-$PWD}" && pwd); cd "$SUBJ"
PIN=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin
FILES="test/xaas/ultracode/court_receipt_test.exs test/xaas/ultracode/semantic_receipt_test.exs test/xaas/sjira/successor_test.exs"
PART=${R2_PARTITION:-_r2host}
GI=${GGEN_IGNITER_DIR:-/Users/sac/wt/v26922/fri/ggen_igniter-int}
L=$(mktemp -d "${TMPDIR:-/tmp}/r2-x-hostskip.XXXXXX")
PATH="$PIN:$PATH"; export PATH
echo "# subject=$SUBJ head=$(git rev-parse HEAD) logs=$L"
elixir --version | tail -1
mix format --check-formatted
MIX_ENV=test mix compile --force --warnings-as-errors
# clause 1: host environment
if ! GGEN_IGNITER_DIR=$GI MIX_ENV=test MIX_TEST_PARTITION=$PART mix test $FILES > "$L/host.log" 2>&1; then
  tail -40 "$L/host.log"; echo "# clause 1 (host) FAILED"; exit 1
fi
# clause 2: hosted-runner-shaped environment (real absence, no doubles)
H=$(mktemp -d "${TMPDIR:-/tmp}/r2-x-hostskip-home.XXXXXX")
SH=$(mktemp -d "${TMPDIR:-/tmp}/r2-x-hostskip-py.XXXXXX")
printf '#!/bin/sh\nexec /usr/bin/python3 -I -S "$@"\n' > "$SH/python3"; chmod +x "$SH/python3"
if "$SH/python3" -c 'import rdflib' 2>/dev/null; then echo "# shim python3 still imports rdflib"; exit 1; fi
if /usr/bin/env -i HOME="$H" PATH="$H/.asdf/installs/elixir/1.18.4-otp-27/bin:$H/.asdf/installs/erlang/27.2.4/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin" mix --version >/dev/null 2>&1; then
  echo "# the format suite's pinned PATH still yields a working mix under the fresh HOME"; exit 1
fi
if ! /usr/bin/env -i HOME="$H" PATH="$PIN:$SH:/usr/bin:/bin" LANG=en_US.UTF-8 \
     MIX_HOME=/Users/sac/.mix HEX_HOME=/Users/sac/.hex MIX_ENV=test MIX_TEST_PARTITION=$PART \
     GGEN_IGNITER_DIR="$H/absent-ggen_igniter" \
     mix test $FILES > "$L/cilike.log" 2>&1; then
  tail -40 "$L/cilike.log"; echo "# clause 2 (hosted-runner shape) FAILED"; exit 1
fi
python3 - "$L/host.log" "$L/cilike.log" <<'PY'
import re, sys
def summary(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    res = [l for l in lines if re.match(r"^Result: \d+(/\d+)? passed", l)]
    std = [l for l in lines if re.search(r"\d+ tests?, \d+ failures?", l)]
    if res:  # xaas's custom ExUnit formatter: "Result: 48/50 passed, 3 skipped" + "Failed: 2 tests"
        line = res[-1]
        fl = [l for l in lines if re.match(r"^Failed: \d+ tests?", l)]
        failures = int(re.search(r"\d+", fl[-1]).group()) if fl else 0
    elif std:
        line = std[-1]
        failures = int(re.search(r"(\d+) failures?", line).group(1))
    else:
        sys.exit(f"no ExUnit summary line in {path}")
    sk = re.search(r"(\d+) skipped", line)
    return line, failures, int(sk.group(1)) if sk else 0
h, c = summary(sys.argv[1]), summary(sys.argv[2])
print("host   :", h[0], "| failures", h[1], "| skipped", h[2])
print("cilike :", c[0], "| failures", c[1], "| skipped", c[2])
ok = h[1] == 0 and h[2] == 0 and c[1] == 0 and c[2] >= 3
print("HOSTSKIP_GATE", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
