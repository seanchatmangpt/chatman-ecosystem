#!/bin/sh
# CE23-0 anti-vacuity of the corpus itself (evidence script, step CE23-0): each court mutant below
# weakens exactly one clause of release/v26.9.23/courts/ce23_0/court.py in place, runs the court, and
# must be caught by the corpus (an AV_MUTANT_ADMITTED or AV_CONTROL_NOT_ALIVE line). The committed
# court is restored byte for byte after every mutant (cmp against a scratch copy; git diff --quiet).
# Exit 0 = every mutant caught and the court restored; 1 otherwise. Run from the chatman-ecosystem root.
set -u
court=release/v26.9.23/courts/ce23_0/court.py
scratch=$(mktemp -d "${TMPDIR:-/tmp}/ce23-0-court-mutants.XXXXXX")
cp "$court" "$scratch/court.py.orig"
fail=0
mutate() {  # id, python replacement old -> new (exactly one occurrence)
  python3 - "$court" "$2" "$3" <<'PY' || exit 1
import sys
path, old, new = sys.argv[1:4]
text = open(path, encoding="utf-8").read()
assert text.count(old) == 1, f"{old!r} occurs {text.count(old)} times"
open(path, "w", encoding="utf-8").write(text.replace(old, new))
PY
  out=$(PYTHONDONTWRITEBYTECODE=1 python3 "$court" 2>&1)
  cp "$scratch/court.py.orig" "$court"
  if ! cmp -s "$scratch/court.py.orig" "$court" || ! git diff --quiet -- "$court"; then
    echo "RESTORE_FAILED $1"; fail=1; return
  fi
  caught=$(printf '%s\n' "$out" | grep -E 'REFUSED\[AV_(MUTANT_ADMITTED|CONTROL_NOT_ALIVE)\]' | head -3)
  if [ -n "$caught" ]; then
    echo "CAUGHT $1:"; printf '%s\n' "$caught" | sed 's/^/    /'
  else
    echo "NOT_CAUGHT $1"; printf '%s\n' "$out" | grep -E '^OK AV|AV:' | sed 's/^/    /'; fail=1
  fi
}
mutate CM1-root-set 'if roots != [s["github_root"]]:' 'if False and roots != [s["github_root"]]:'
mutate CM2-publication 'if published != ll["published"]:' 'if False and published != ll["published"]:'
mutate CM3-receipt-claims '    if mismatch:
        j.refuse("RECEIPT_CLAIM_MISMATCH"' '    if False and mismatch:
        j.refuse("RECEIPT_CLAIM_MISMATCH"'
mutate CM4-diverged-line 'j.refuse("BRANCH_DIVERGED", "I4"' 'j.ok("I4"'
mutate CM5-shadow-continuation 'if broken:
        j.refuse("SHADOW_LINE_NOT_CONTINUED"' 'if False and broken:
        j.refuse("SHADOW_LINE_NOT_CONTINUED"'
mutate CM6-evidence-rule 'if not any(observed.values()) and not chk and not all(objects.values()):' 'if not any(observed.values()) and not chk:'
# skeptic repair r1 (R1 admission hole): each weakening below must be caught by the new corpus mutants
mutate CM7-unmarked-receipt 'j.refuse("RECEIPT_NOT_COURT_EMITTED", "R1", ' 'j.ok("R1", '
mutate CM8-exemption-unpinned 'if record["blob"] in superseded:' 'if True:'
mutate CM9-court-digest '    if court_off:
        j.refuse("RECEIPT_COURT_MISMATCH"' '    if False and court_off:
        j.refuse("RECEIPT_COURT_MISMATCH"'
mutate CM10-standing-derivation '    if underived:
        j.refuse("RECEIPT_STANDING_UNDERIVED"' '    if False and underived:
        j.refuse("RECEIPT_STANDING_UNDERIVED"'
mutate CM11-supersession 'mismatch.append("supersedes (not the receipt at its subject)")' 'pass'
rm -rf "$scratch"
n=$(grep -c '^mutate CM' "$0")
[ "$fail" -eq 0 ] && echo "COURT_MUTANTS CAUGHT $n/$n" || echo "COURT_MUTANTS FAILED"
exit "$fail"
