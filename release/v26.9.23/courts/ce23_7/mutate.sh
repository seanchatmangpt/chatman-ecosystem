#!/usr/bin/env bash
# CE23-7 court anti-vacuity corpus (release/v26.9.23/courts/ce23_7/court.py).
#
# Each mutant is `git archive <SUBJECT>` of the repository that holds this file, extracted into
# $M/<id>, committed in a fresh tmp git repo, mutated, committed, and judged by the court it
# carries. M0 (unmutated) must be ALIVE (exit 0); every other mutant must print the typed line
# its judge names and exit with the judge's code (1 REFUSED, 75 UNKNOWN). Exit 0 iff all hold.
#
#   SUBJECT  commit to archive (default: HEAD of the repository holding this file)
#   M        scratch directory (default: a fresh mktemp dir; an existing non-empty M must carry
#            the .ce23-7-mutants marker this script writes, or it is refused)
#   ONLY     space-separated mutant ids to run (default: all)
#
# The MX* mutants read v26.9.1 through channels the court's first probe did not judge
# (skeptic refutation of CE23-7, 2026-09-24): a repository-anchored pointer read (MX1, the
# skeptic's mutant; MX1b in the root-crown state, pointer and West projection on v26.9.23,
# whose control M0b must stay ALIVE), a child
# process (MX2), a byte copy under another name (MX3), a directory listing (MX4), an unaudited
# child (MX5), native code (MX6), the git object store (MX7) and a URL (MX8). None names the
# predecessor as a literal (the fenced-tool token scan, F7, stays silent on all of them).
set -u
here=$(cd "$(dirname "$0")" && pwd)
SRC=$(git -C "$here" rev-parse --show-toplevel) || { echo "UNKNOWN[NOT_A_CHECKOUT] mutate: $here"; exit 75; }
HEAD_SHA=${SUBJECT:-$(git -C "$SRC" rev-parse HEAD)}
BASE=aa4e3873b40c3406378800ca82facc366293b564
if [ -z "${M:-}" ]; then
  M=$(mktemp -d "${TMPDIR:-/tmp}/ce23-7-mutants.XXXXXX")
elif [ -d "$M" ] && [ -n "$(ls -A "$M")" ] && [ ! -f "$M/.ce23-7-mutants" ]; then
  echo "REFUSED[SCRATCH_NOT_OURS] mutate: $M is non-empty and carries no .ce23-7-mutants marker"; exit 2
else
  rm -rf "$M"; mkdir -p "$M"
fi
touch "$M/.ce23-7-mutants"
FAIL=0
export PYTHONDONTWRITEBYTECODE=1
echo "CE23-7 mutants: subject $HEAD_SHA from $SRC into $M"

want() { [ -z "${ONLY:-}" ] && return 0; case " $ONLY " in *" $1 "*) return 0;; esac; return 1; }
mk() {  # mk <id>: materialize SUBJECT into $M/<id> as a committed tmp repo
  local d="$M/$1"; mkdir -p "$d"
  git -C "$SRC" archive "$HEAD_SHA" | tar -x -C "$d"
  git -C "$d" init -q && git -C "$d" add -A -f && git -C "$d" -c user.name=court -c user.email=court@localhost commit -qm "archive $HEAD_SHA"
}
commit() { git -C "$M/$1" add -A -f && git -C "$M/$1" -c user.name=court -c user.email=court@localhost commit -qm "mutant $1"; }
judge() {  # judge <id> <expected-exit> <expected-line-regex>
  local d="$M/$1"; (cd "$d" && sh release/v26.9.23/courts/CE23-7.sh > "$M/$1.log" 2>&1); local rc=$?
  local hit; hit=$(grep -E "$3" "$M/$1.log" | head -2 | cut -c1-240)
  echo "MUTANT $1 exit=$rc expect=[exit $2, $3] witnessed=[${hit:-NONE}] final=$(tail -1 "$M/$1.log")"
  if [ -z "$hit" ] || [ "$rc" != "$2" ]; then FAIL=1; fi
}
no_token() {  # the mutated file must not name the predecessor (F7 cannot be what catches it)
  if python3 -c 'import re,sys; sys.exit(0 if re.search(r"26[._-]9[._-]1(?![0-9])", open(sys.argv[1]).read()) else 1)' "$1"; then
    echo "MUTANT-SETUP $1 names the predecessor token"; FAIL=1
  fi
}
inject() {  # inject <id> <python-body>: add <python-body> at the top of verify() (standing verifier)
  python3 - "$M/$1/scripts/verify_standing_evidence.py" "$2" <<'PY'
import sys
p, body = sys.argv[1], sys.argv[2]
t = open(p).read()
old = "def verify(path: Path) -> dict[str, Any]:\n"
assert t.count(old) == 1, "anchor"
lines = "".join("    " + line + "\n" for line in body.splitlines())
open(p, "w").write(t.replace(old, old + lines))
PY
  no_token "$M/$1/scripts/verify_standing_evidence.py"
}
crown_flip() {  # crown_flip <id>: the root-crown state, catalog pointer and West projection on v26.9.23
  python3 - "$M/$1" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1]); cat = root / "catalog" / "west.toml"
new, n = re.subn(r'(?m)^release_manifest = "release/v26\.9\.1/manifest\.toml"$', 'release_manifest = "release/v26.9.23/manifest.toml"', cat.read_text())
assert n == 1; cat.write_text(new)
for f in [root / "west.yml", *sorted((root / "west").glob("*.yml"))]:
    f.write_text(f.read_text().replace("source: release/v26.9.1/manifest.toml", "source: release/v26.9.23/manifest.toml"))
PY
}
REPO='_repo = Path(__file__).resolve().parents[1]'
LEGACY='_legacy = _repo / "release" / ("v26." + "9.1") / "manifest.toml"'

if want M0; then mk M0; judge M0 0 'CE23-7 ALIVE'; fi

if want M1; then
  mk M1
  for s in verify_release plan_completion survey_portfolio verify_standing_evidence verify_west_workspace; do
    git -C "$SRC" show "$BASE:scripts/$s.py" > "$M/M1/scripts/$s.py"
  done
  commit M1; judge M1 1 'REFUSED\[(FENCED_TOOL_NAMES_PREDECESSOR|FALSIFIER_ADMITTED|SILENT_V26_9_1_READ|OUTPUT_NOT_BOUND)'
fi

if want M2; then  # version-path law disabled
  mk M2
  python3 - "$M/M2/scripts/verify_release.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = "            elif version != expected:\n"
assert t.count(old) == 1; open(p, "w").write(t.replace(old, "            elif False:\n"))
PY
  commit M2; judge M2 1 'REFUSED\[FALSIFIER_ADMITTED\] F5a'
fi

if want M3; then  # planner branch prefix bound to the predecessor without a literal
  mk M3
  python3 - "$M/M3/scripts/plan_completion.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = '    return f"agent/v{version}-{slug}-{suffix}"\n'
assert t.count(old) == 1; open(p, "w").write(t.replace(old, '    return f"agent/v26.{9}.{1}-{slug}-{suffix}"\n'))
PY
  commit M3; judge M3 1 'REFUSED\[OUTPUT_NOT_BOUND\] F4'
fi

if want M4; then  # hidden cwd-relative v26.9.1 read
  mk M4
  inject M4 '_legacy = Path("release") / ("v26." + "9.1") / "manifest.toml"
if _legacy.is_file():
    _legacy.read_bytes()'
  commit M4; judge M4 1 'REFUSED\[SILENT_V26_9_1_READ\] F4'
fi

if want M5; then  # West release-source binding disabled
  mk M5
  python3 - "$M/M5/scripts/verify_west_workspace.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = "    if foreign_source:\n"
assert t.count(old) == 1; open(p, "w").write(t.replace(old, "    if foreign_source and False:\n"))
PY
  commit M5; judge M5 1 'REFUSED\[FALSIFIER_ADMITTED\] F5d'
fi

if want M6; then  # new unledgered script with a v26.9.1 default
  mk M6
  printf '#!/usr/bin/env python3\nfrom pathlib import Path\nDEFAULT = Path("release/v26.9.1/manifest.toml")\n' > "$M/M6/scripts/new_tool.py"
  commit M6; judge M6 1 'REFUSED\[UNLEDGERED_V26_9_1_BINDING\]'
fi

if want M7; then  # release/v26.9.1 touched
  mk M7
  printf '\n' >> "$M/M7/release/v26.9.1/fleet-policy.toml"
  commit M7; judge M7 1 'REFUSED\[PREDECESSOR_TOUCHED\]'
fi

if want M8; then  # survey census scope bound to the predecessor without a literal
  mk M8
  python3 - "$M/M8/scripts/survey_portfolio.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = '            scope = "REQUIRED_" + release_label(manifest).upper().replace(".", "_")\n'
assert t.count(old) == 1; open(p, "w").write(t.replace(old, '            scope = "REQUIRED_V26_" + "9_1"\n'))
PY
  commit M8; judge M8 1 'REFUSED\[(OUTPUT_NOT_BOUND|FENCED_TOOL_NAMES_PREDECESSOR)'
fi

if want MX1; then  # the skeptic's mutant: read the manifest the tool's own repository pointer declares
  mk MX1
  inject MX1 "$REPO"'
_legacy = _repo / release_line.declared_manifest(_repo)
if _legacy.is_file():
    _legacy.read_bytes()'
  commit MX1; judge MX1 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .* opened .*/release/v26\.9\.1/manifest\.toml'
fi

if want M0b; then  # control: the unmutated subject in the root-crown state (pointer + West on v26.9.23) is ALIVE
  mk M0b; crown_flip M0b; commit M0b; judge M0b 0 'CE23-7 ALIVE'
fi

if want MX1b; then  # MX1 in the root-crown state: only the self-hosted run can see the v26.9.1 read
  mk MX1b
  inject MX1b "$REPO"'
_legacy = _repo / release_line.declared_manifest(_repo)
if _legacy.is_file():
    _legacy.read_bytes()'
  crown_flip MX1b
  commit MX1b; judge MX1b 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: pointer->v26\.9\.1 \(self-hosted\): verify_standing_evidence'
fi

if want MX2; then  # a child process reads the predecessor manifest
  mk MX2
  inject MX2 "$REPO"'
'"$LEGACY"'
import subprocess
subprocess.run(["cat", str(_legacy)], capture_output=True, check=False)'
  commit MX2; judge MX2 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .*spawned a child process naming v26\.9\.1'
fi

if want MX3; then  # a byte copy of the predecessor manifest under another name (not a .py file)
  mk MX3
  cp "$M/MX3/release/v26.9.1/manifest.toml" "$M/MX3/scripts/legacy_inputs.toml"
  inject MX3 '(Path(__file__).resolve().parent / "legacy_inputs.toml").read_bytes()'
  commit MX3; judge MX3 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .*a byte copy of a release/v26\.9\.1 file'
fi

if want MX4; then  # a directory listing of the predecessor line
  mk MX4
  inject MX4 "$REPO"'
import os
os.listdir(_repo / "release" / ("v26." + "9.1"))'
  commit MX4; judge MX4 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .*read the directory .*/release/v26\.9\.1'
fi

if want MX5; then  # a child process the probe cannot see into (no predecessor in its argv)
  mk MX5
  inject MX5 'import subprocess
subprocess.run(["true"], check=False)'
  commit MX5; judge MX5 75 'UNKNOWN\[PROBE_BLIND\] F4: .*spawned a child process the audit hook cannot see into'
fi

if want MX6; then  # native code opens the predecessor manifest without an open audit event
  mk MX6
  inject MX6 "$REPO"'
'"$LEGACY"'
import ctypes
_libc = ctypes.CDLL(None)
_fd = _libc.open(str(_legacy).encode(), 0)
if _fd >= 0:
    _libc.close(_fd)'
  commit MX6; judge MX6 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .*ran native code \(ctypes\) naming v26\.9\.1'
fi

if want MX7; then  # the git object store of the tool's repository
  mk MX7
  inject MX7 "$REPO"'
_head = _repo / ".git" / "HEAD"
if _head.is_file():
    _head.read_bytes()'
  commit MX7; judge MX7 75 'UNKNOWN\[PROBE_BLIND\] F4: .*in a git object store'
fi

if want MX8; then  # a URL naming the predecessor line (loopback, closed port)
  mk MX8
  inject MX8 'import urllib.request
try:
    urllib.request.urlopen("http://127.0.0.1:9/release/v26." + "9.1/manifest.toml", timeout=2)
except OSError:
    pass'
  commit MX8; judge MX8 1 'REFUSED\[SILENT_V26_9_1_READ\] F4: .*requested http://127\.0\.0\.1:9/release/v26\.9\.1/manifest\.toml'
fi

echo "MUTATION WITNESSES $([ "$FAIL" = 0 ] && echo HOLD || echo FAILED) subject=$HEAD_SHA"
exit "$FAIL"
