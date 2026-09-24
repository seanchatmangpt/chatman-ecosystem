#!/usr/bin/env bash
# Anti-vacuity witnesses for the CE23-7 court (receipts/v26.9.23/CE23-7.json): each mutant is
# `git archive <SUBJECT>` of the canonical checkout into scratch, committed in a fresh tmp git
# repo, mutated, then judged by the court it carries. M0 (unmutated) must be ALIVE; every other
# mutant must be refused with the typed code named in its judge line. Exit 0 iff all hold.
#   SUBJECT (default: the CE23-7 fence commit), SRC (canonical checkout), M (scratch dir).
set -u
SRC=${SRC:-/Users/sac/chatman-ecosystem}
HEAD_SHA=${SUBJECT:-e3a51dc5a06a8f9bad4764269f8ef8f76f0e3a32}
BASE=aa4e3873b40c3406378800ca82facc366293b564
M=${M:-/private/tmp/claude-501/v23-scratch/FIN2-CE23-7/mut}
FAIL=0
rm -rf "$M"; mkdir -p "$M"
export PYTHONDONTWRITEBYTECODE=1

mk() {  # mk <id>: materialize HEAD into $M/<id> as a committed tmp repo
  local d="$M/$1"; mkdir -p "$d"
  git -C "$SRC" archive "$HEAD_SHA" | tar -x -C "$d"
  git -C "$d" init -q && git -C "$d" add -A -f && git -C "$d" -c user.name=court -c user.email=court@localhost commit -qm "archive $HEAD_SHA"
}
commit() { git -C "$M/$1" -c user.name=court -c user.email=court@localhost commit -qam "mutant $1"; }
judge() {  # judge <id> <expected-code-regex>
  local d="$M/$1"; (cd "$d" && sh release/v26.9.23/courts/CE23-7.sh > "$M/$1.log" 2>&1); local rc=$?
  local hit; hit=$(grep -E "$2" "$M/$1.log" | head -2 | cut -c1-220)
  echo "MUTANT $1 exit=$rc expect=[$2] witnessed=[${hit:-NONE}] final=$(tail -1 "$M/$1.log")"
  if [ -z "$hit" ]; then FAIL=1; fi
  if [ "$1" = M0 ] && [ "$rc" != 0 ]; then FAIL=1; fi
  if [ "$1" != M0 ] && [ "$rc" != 1 ]; then FAIL=1; fi
}

mk M0; judge M0 'CE23-7 ALIVE'

mk M1
for s in verify_release plan_completion survey_portfolio verify_standing_evidence verify_west_workspace; do
  git -C "$SRC" show "$BASE:scripts/$s.py" > "$M/M1/scripts/$s.py"
done
commit M1; judge M1 'REFUSED\[(FENCED_TOOL_NAMES_PREDECESSOR|FALSIFIER_ADMITTED|SILENT_V26_9_1_READ|OUTPUT_NOT_BOUND)'

mk M2
python3 - "$M/M2/scripts/verify_release.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = "        elif version != expected:\n"
assert t.count(old) == 1; open(p, "w").write(t.replace(old, "        elif False:\n"))
PY
commit M2; judge M2 'REFUSED\[FALSIFIER_ADMITTED\] F5a'

mk M3
python3 - "$M/M3/scripts/plan_completion.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = '    return f"agent/v{version}-{slug}-{suffix}"\n'
assert t.count(old) == 1; open(p, "w").write(t.replace(old, '    return f"agent/v26.{9}.{1}-{slug}-{suffix}"\n'))
PY
commit M3; judge M3 'REFUSED\[OUTPUT_NOT_BOUND\] F4'

mk M4
python3 - "$M/M4/scripts/verify_standing_evidence.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = "def verify(path: Path) -> dict[str, Any]:\n"
new = old + '    legacy = Path("release") / ("v26." + "9.1") / "manifest.toml"\n    if legacy.is_file():\n        legacy.read_bytes()\n'
assert t.count(old) == 1; open(p, "w").write(t.replace(old, new))
PY
commit M4; judge M4 'REFUSED\[SILENT_V26_9_1_READ\]'

mk M5
python3 - "$M/M5/scripts/verify_west_workspace.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = "    if foreign_source:\n"
assert t.count(old) == 1; open(p, "w").write(t.replace(old, "    if foreign_source and False:\n"))
PY
commit M5; judge M5 'REFUSED\[FALSIFIER_ADMITTED\] F5d'

mk M6
printf '#!/usr/bin/env python3\nfrom pathlib import Path\nDEFAULT = Path("release/v26.9.1/manifest.toml")\n' > "$M/M6/scripts/new_tool.py"
git -C "$M/M6" add scripts/new_tool.py; commit M6; judge M6 'REFUSED\[UNLEDGERED_V26_9_1_BINDING\]'

mk M7
printf '\n' >> "$M/M7/release/v26.9.1/fleet-policy.toml"
commit M7; judge M7 'REFUSED\[PREDECESSOR_TOUCHED\]'

mk M8
python3 - "$M/M8/scripts/survey_portfolio.py" <<'PY'
import sys; p = sys.argv[1]; t = open(p).read()
old = '            scope = "REQUIRED_" + release_label(manifest).upper().replace(".", "_")\n'
assert t.count(old) == 1; open(p, "w").write(t.replace(old, '            scope = "REQUIRED_V26_" + "9_1"\n'))
PY
commit M8; judge M8 'REFUSED\[(OUTPUT_NOT_BOUND|FENCED_TOOL_NAMES_PREDECESSOR)'
echo "MUTATION WITNESSES $([ "$FAIL" = 0 ] && echo HOLD || echo FAILED) subject=$HEAD_SHA"
exit "$FAIL"
