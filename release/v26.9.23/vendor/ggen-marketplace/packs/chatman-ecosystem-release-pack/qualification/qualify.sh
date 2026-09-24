#!/usr/bin/env bash
# Chicago-style pack qualification (real ggen, real rdflib, real files; no mocks).
# Everything runs in a scratch copy; the committed tree is never written.
#   1. qualification/consumer.ttl passes the explicit runner.
#   2. consumer-v26.9.23 passes native `ggen sync run` twice with byte-identical
#      outputs, passes the runner, and renders 16 disposed legacy roles.
#   3. control = consumer-v26.9.23 minus the CE orders import (the mutant base)
#      passes both executors; M6's committed file differs from the control render
#      in exactly the forged standing line.
#   4. a valid explicit decision (positive witness) is admitted and rendered.
#   5. every mutant in mutants/EXPECTED.tsv is refused by the declared executor
#      with the declared code, gate and reason.
#   6. imported crown (gate 090): every committed qualification/imported-crown.*.ttl is
#      the lift of its fixtures/<name>-receipts dir; the lift refuses 0 or 2 STOP receipts;
#      the positive crown passes both executors through bin/import-crown-generate.sh and
#      its committed lift + render reproduce, while a hand-edited render or a stale lift is
#      refused; every row of imported-crown.EXPECTED.tsv is returned by gate 090 (exact row
#      count), refused natively (FM-PACK-013 at gate 090), and admitted once gate 090 is
#      removed (the refusal comes from gate 090). XAAS_REPO=<xaas checkout> also re-derives
#      the fixtures byte-identically from the real receipt blobs.
# Usage: qualification/qualify.sh   (GGEN=<ggen binary> to override)
set -u
P=$(cd "$(dirname "$0")/.." && pwd)
GGEN=${GGEN:-ggen}
W=$(mktemp -d "${TMPDIR:-/tmp}/relpack-qual.XXXXXX")
fail=0
ok() { printf 'PASS %s\n' "$*"; }
no() { printf 'FAIL %s\n' "$*"; fail=1; }

# Copy a consumer dir into scratch and point its path pack at this pack (absolute).
# A third argument "keep-out" preserves a committed out/ fixture (M6); otherwise
# any previous sync consequence is dropped so every render is fresh.
stage() {
  cp -R "$1" "$2"
  rm -rf "$2/.ggen-v2" "$2/.ggen" "$2/ggen.lock"
  if [ "${3:-}" != keep-out ]; then rm -rf "$2/out"; fi
  python3 - "$2/ggen.toml" "$P" <<'PY'
import re, sys
path, pack = sys.argv[1], sys.argv[2]
text = open(path).read()
text, n = re.subn(r'path = "[^"]+"', f'path = "{pack}"', text)
assert n == 1, n
open(path, "w").write(text)
PY
}

runner() { python3 "$P/bin/run-gates.py" "$1/release.ttl" "$P/gates" > "$2" 2>&1; }

# 1
if python3 "$P/bin/run-gates.py" "$P/qualification/consumer.ttl" "$P/gates" > "$W/consumer.log" 2>&1; then
  ok "consumer.ttl runner"; else no "consumer.ttl runner (see $W/consumer.log)"; fi

# 2
stage "$P/qualification/consumer-v26.9.23" "$W/c23"
if (cd "$W/c23" && "$GGEN" sync run > "$W/c23-1.json" 2> "$W/c23-1.err"); then ok "c23 sync 1"; else no "c23 sync 1"; fi
cp -R "$W/c23/out" "$W/c23-out1"
if (cd "$W/c23" && "$GGEN" sync run > "$W/c23-2.json" 2> "$W/c23-2.err"); then ok "c23 sync 2"; else no "c23 sync 2"; fi
if diff -r "$W/c23/out" "$W/c23-out1" > /dev/null; then ok "c23 renders byte-identical"; else no "c23 renders differ"; fi
if runner "$W/c23" "$W/c23-runner.log"; then ok "c23 runner"; else no "c23 runner"; fi
if python3 - "$W/c23/out" <<'PY'
import sys, tomllib
from pathlib import Path
from rdflib import Graph, URIRef
out = Path(sys.argv[1])
docs = {p.name: tomllib.loads(p.read_text()) for p in out.glob("*.toml")}
xw = docs["legacy-role-crosswalk.toml"]
roles = xw["role"]
assert xw["crosswalk"]["role_count"] == 16 == len(roles) == len({r["legacy_role"] for r in roles}), len(roles)
assert all(r["boundary"] in {"REQUIRED", "SUCCESSOR", "BLOCKED", "UNSUPPORTED", "REFUSED"} for r in roles)
assert all(r["reason"] and (r["derived_by"] or r["decided_by"]) for r in roles)
manifest = docs["manifest.toml"]
fields = {"id", "repository", "ref", "ref_check", "sha", "role", "disposition", "standing", "required", "depends_on"}
assert all(fields <= set(c) for c in manifest["components"]), manifest["components"]
mapped = {c["release_role"] for c in docs["constitutional-role-crosswalk.toml"]["crosswalk"]}
assert {c["role"] for c in manifest["components"] if c["required"]} <= mapped
assert docs["requirements.toml"]["requirements"]["row_count"] == len(docs["requirements.toml"]["requirement"]) > 0
g = Graph().parse(out / "crosswalk.ttl")
er = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
assert len(set(g.subjects(URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef(er + "RoleDisposition")))) == 16
print("rendered: 16 roles disposed, manifest fields complete, roles mapped, requirements", docs["requirements.toml"]["requirements"]["row_count"])
PY
then ok "c23 rendered contents"; else no "c23 rendered contents"; fi

# 3
stage "$P/qualification/consumer-v26.9.23" "$W/control"
sed -i.bak 's#, "imports/ce23-orders.ttl"##' "$W/control/ggen.toml" && rm "$W/control/ggen.toml.bak" "$W/control/imports/ce23-orders.ttl"
if (cd "$W/control" && "$GGEN" sync run > "$W/control.json" 2> "$W/control.err"); then ok "control sync"; else no "control sync"; fi
if runner "$W/control" "$W/control-runner.log"; then ok "control runner"; else no "control runner"; fi
changed=$(diff "$W/control/out/manifest.toml" "$P/qualification/mutants/M6-hand-edited-rendered-file/out/manifest.toml" | grep -c '^[<>]')
if [ "$changed" = 2 ] && diff "$W/control/out/manifest.toml" "$P/qualification/mutants/M6-hand-edited-rendered-file/out/manifest.toml" | grep -q '^> standing = "ALIVE"'; then
  ok "M6 differs from the control render only in the forged standing"; else no "M6 fixture drifted from the control render ($changed changed lines)"; fi

# 4
stage "$W/control" "$W/decision"
cat >> "$W/decision/release.ttl" <<'TTL'

<https://ggen.dev/marketplace/qualification/chatman-ecosystem-release/v26.9.23/release/decision/formal-proof> a er:RoleDisposition ;
    er:legacyRole "formal-proof" ;
    er:sourceRelease <https://github.com/seanchatmangpt/chatman-ecosystem/release/v26.9.1> ;
    er:targetRelease <https://ggen.dev/marketplace/qualification/chatman-ecosystem-release/v26.9.23/release> ;
    er:boundary er:ROLE_BLOCKED ;
    er:reason "qualification witness: an explicit decision for a repository absent from the fleet classification" ;
    er:decidedBy "qualification:positive-witness" .
TTL
if (cd "$W/decision" && "$GGEN" sync run > "$W/decision.json" 2> "$W/decision.err") && runner "$W/decision" "$W/decision-runner.log" \
  && python3 - "$W/decision/out" <<'PY'
import sys, tomllib
from pathlib import Path
out = Path(sys.argv[1])
rows = {r["legacy_role"]: r for r in tomllib.loads((out / "legacy-role-crosswalk.toml").read_text())["role"]}
assert len(rows) == 16
fp = rows["formal-proof"]
assert (fp["boundary"], fp["decided_by"], fp["derived_by"]) == ("BLOCKED", "qualification:positive-witness", ""), fp
assert tomllib.loads((out / "role-derivations.toml").read_text())["derivations"]["decided_count"] == 1
PY
then ok "explicit decision admitted and rendered"; else no "explicit decision witness"; fi

# 5
while IFS=$'\t' read -r name code gate want reason; do
  case "$name" in ''|'#'*) continue ;; esac
  stage "$P/qualification/mutants/$name" "$W/m-$name" keep-out
  (cd "$W/m-$name" && "$GGEN" sync run > "$W/m-$name.json" 2> "$W/m-$name.err"); r=$?
  runner "$W/m-$name" "$W/m-$name.runner.log"; g=$?
  verdict=ok
  [ "$r" -ne 0 ] && grep -q "\[$code\]" "$W/m-$name.err" || verdict=no
  if [ "$gate" != "-" ]; then grep -q "gate \`$gate\`" "$W/m-$name.err" || verdict=no; fi
  if [ "$want" = REFUSED ]; then
    [ "$g" -ne 0 ] && grep -q -- "$reason" "$W/m-$name.runner.log" || verdict=no
  else
    [ "$g" -eq 0 ] || verdict=no
  fi
  if [ "$verdict" = ok ]; then ok "$name native=$r[$code] runner=$g"; else no "$name native=$r runner=$g (see $W/m-$name.*)"; fi
done < "$P/qualification/mutants/EXPECTED.tsv"

# 6. imported upstream crown (0.3.0, gate 090, bin/import-crown-*)
X="$P/qualification/fixtures"
crown_reasons() { python3 - "$P" "$1" "$2" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("run_gates", Path(sys.argv[1]) / "bin/run-gates.py")
rg = importlib.util.module_from_spec(spec); spec.loader.exec_module(rg)
for row in rg.union_graph(Path(sys.argv[2])).query(Path(sys.argv[3]).read_text()):
    print(row[1])
PY
}
lifted() { python3 "$P/bin/import-crown-lift.py" "$X/$1-receipts" "$(cat "$X/$1-receipts/XAAS_SHA")" "$(cat "$X/$1-receipts/GI_SHA")"; }
stage_crown() { # <dest> <crown ttl>: the crown consumer with a given committed lift
  stage "$P/qualification/consumer-imported-crown" "$1"; cp "$2" "$1/imported/crown.ttl"; }
# 6a committed lifts are the lift of their fixture dirs
for f in positive stale-r0 llm1 unreceipted-null drop-gate foreign-subject gi-mismatch; do
  if lifted "$f" | cmp -s - "$P/qualification/imported-crown.$f.ttl"; then ok "lift $f == committed"; else no "lift $f drifted from qualification/imported-crown.$f.ttl"; fi
done
cmp -s "$P/qualification/consumer-imported-crown/imported/crown.ttl" "$P/qualification/imported-crown.positive.ttl" \
  && ok "crown consumer input == positive lift" || no "crown consumer input drifted"
# 6b fixture provenance replay from real xaas git objects (named skip without a checkout)
if [ -n "${XAAS_REPO:-}" ]; then
  if python3 "$X/derive-fixtures.py" "$XAAS_REPO" "$W/fixtures" > "$W/derive.log" 2>&1 && diff -r -x derive-fixtures.py -x SOURCES.md "$W/fixtures" "$X" > /dev/null; then
    ok "fixtures re-derived byte-identical from $XAAS_REPO"; else no "fixture re-derivation (see $W/derive.log)"; fi
else echo "SKIP fixture re-derivation: set XAAS_REPO=<xaas checkout with 4b14e3f and 66b52e7>"; fi
# 6c lift guards: exactly one STOP receipt
mkdir -p "$W/lift-empty" "$W/lift-two"; cp "$X"/positive-receipts/*.json "$W/lift-two/"
cp "$X/stale-r0-receipts/STOP-GC-26.9.23.json" "$W/lift-two/STOP-R0.json"
for d in lift-empty lift-two; do
  if python3 "$P/bin/import-crown-lift.py" "$W/$d" a b > /dev/null 2>&1; then no "lift accepted $d"; else ok "lift refuses $d"; fi
done
# 6d positive: both executors admit, render twice identically, drift is refused
gen() { F="$X/$1-receipts"; bash "$P/bin/import-crown-generate.sh" "$F" "$(cat "$F/XAAS_SHA")" "$(cat "$F/GI_SHA")" "$2" "$3" > "$3.log" 2>&1; }
stage_crown "$W/crown" "$P/qualification/imported-crown.positive.ttl"
gen positive "$W/crown" "$W/crown-g1"; r=$?
[ "$r" = 3 ] && grep -q IMPORTED_CROWN_UNCOMMITTED "$W/crown-g1.log" && ok "first render reports uncommitted (exit 3)" || no "first render exit $r"
mkdir -p "$W/crown/out"; cp "$W/crown-g1/out/imported-crown.toml" "$W/crown/out/"
gen positive "$W/crown" "$W/crown-g2" && grep -q IMPORTED_CROWN_IDENTICAL_ALIVE "$W/crown-g2.log" \
  && ok "committed lift + render reproduce (IDENTICAL_ALIVE)" || no "positive generate (see $W/crown-g2.log)"
if python3 - "$W/crown-g2/out/imported-crown.toml" "$X/positive-receipts" <<'PY'
import hashlib, sys, tomllib
from pathlib import Path
doc, d = tomllib.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
[c] = doc["imported_crown"]
digest = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
assert doc["imported_crowns"]["crown_count"] == 1 and c["stop_standing"] == "ALIVE"
assert c["LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH"] == 0 == c["UNRECEIPTED_ACTUATION"]
assert c["stop_subject_sha"] == c["crown_commit_sha"] == (d / "XAAS_SHA").read_text().strip()
assert c["paired_commit_sha"] == (d / "GI_SHA").read_text().strip()
assert c["stop_receipt_sha256"] == digest(d / "STOP-GC-26.9.23.json")
gates = {g["id"]: g for g in c["gate"]}
assert len(c["gate"]) == len(gates) == c["required_gate_count"] == 13
assert all(g["receipt_sha256"] == digest(d / f"{i}.json") and g["standing"] == "ALIVE" for i, g in gates.items())
print("rendered: STOP ALIVE, 13 gate digests match the receipt bytes, counters 0")
PY
then ok "crown render contents"; else no "crown render contents"; fi
cp -R "$W/crown" "$W/crown-forged"; sed -i.bak 's/^UNRECEIPTED_ACTUATION = 0$/UNRECEIPTED_ACTUATION = 1/' "$W/crown-forged/out/imported-crown.toml"
gen positive "$W/crown-forged" "$W/crown-g3"; r=$?
[ "$r" = 1 ] && grep -q IMPORTED_CROWN_RENDER_DRIFT "$W/crown-g3.log" && ok "hand-edited render refused (RENDER_DRIFT)" || no "forged render exit $r"
stage_crown "$W/crown-stale-lift" "$P/qualification/imported-crown.llm1.ttl"
gen positive "$W/crown-stale-lift" "$W/crown-g4"; r=$?
[ "$r" = 1 ] && grep -q IMPORTED_CROWN_LIFT_DRIFT "$W/crown-g4.log" && ok "committed lift not matching the receipts refused (LIFT_DRIFT)" || no "lift drift exit $r"
python3 "$P/bin/run-gates.py" "$P/qualification/imported-crown.positive.ttl" "$P/gates" > "$W/crown-positive.log" 2>&1 \
  && ok "positive lift runner" || no "positive lift runner"
# 6e mutants: gate 090 reasons (runner) and FM-PACK-013 at gate 090 (native)
python3 - "$P/qualification/imported-crown.positive.ttl" "$W" <<'PY'
import sys
from rdflib import Graph, URIRef
er = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
for name, prop in (("no-required-count", "requiredGateCount"), ("no-stop-digest", "stopReceiptSha256"), ("no-gate-digest", "receiptSha256")):
    g = Graph().parse(sys.argv[1], format="turtle")
    s = min(g.subjects(URIRef(er + prop), None))
    g.remove((s, URIRef(er + prop), None))
    g.serialize(f"{sys.argv[2]}/imported-crown.{name}.ttl", format="nt", encoding="utf-8")
PY
cp -R "$P" "$W/pack-no090"; rm "$W/pack-no090/gates/090_imported_crown.rq"
while IFS=$'\t' read -r name src rows reason; do
  case "$name" in ''|'#'*) continue ;; esac
  ttl="$P/qualification/imported-crown.$name.ttl"; [ "$src" = lift ] || ttl="$W/imported-crown.$name.ttl"
  crown_reasons "$ttl" "$P/gates/090_imported_crown.rq" > "$W/m-crown-$name.rows"
  got=$(wc -l < "$W/m-crown-$name.rows" | tr -d ' ')
  if [ ! -d "$W/m-crown-$name" ]; then
    stage_crown "$W/m-crown-$name" "$ttl"
    (cd "$W/m-crown-$name" && "$GGEN" sync run > "$W/m-crown-$name.json" 2> "$W/m-crown-$name.err"); echo $? > "$W/m-crown-$name.native"
    python3 "$W/pack-no090/bin/run-gates.py" "$ttl" "$W/pack-no090/gates" > "$W/m-crown-$name.no090" 2>&1; echo $? > "$W/m-crown-$name.revert"
  fi
  n=$(cat "$W/m-crown-$name.native"); rv=$(cat "$W/m-crown-$name.revert")
  if [ "$got" = "$rows" ] && grep -qxF -- "$reason" "$W/m-crown-$name.rows" && [ "$n" != 0 ] \
     && grep -q '\[FM-PACK-013\]' "$W/m-crown-$name.err" && grep -q 'gate `090_imported_crown.rq`' "$W/m-crown-$name.err" && [ "$rv" = 0 ]; then
    ok "crown mutant $name: $reason (rows=$got native=$n[FM-PACK-013 090] without-090=$rv)"
  else no "crown mutant $name: want $reason rows=$rows, got rows=$got native=$n without-090=$rv (see $W/m-crown-$name.*)"; fi
done < "$P/qualification/imported-crown.EXPECTED.tsv"

printf 'QUALIFICATION %s scratch=%s\n' "$([ $fail = 0 ] && echo ALIVE || echo REFUSED)" "$W"
exit $fail
