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
#      with the declared code, gate and reason; each graph mutant is also run through the
#      runner without its named gate and is admitted exactly when no other gate refused it
#      (M3 and M5 are also refused by gate 080).
#   6. imported crown (gate 090): every committed qualification/imported-crown.*.ttl is
#      the lift of its fixtures/<name>-receipts dir; the lift refuses 0 or 2 STOP receipts;
#      the positive crown passes both executors through bin/import-crown-generate.sh and
#      its committed lift + render reproduce, while a hand-edited render or a stale lift is
#      refused; every row of imported-crown.EXPECTED.tsv is returned by gate 090 (exact row
#      count), refused natively (FM-PACK-013 at gate 090), and admitted once gate 090 is
#      removed (the refusal comes from gate 090). XAAS_REPO=<xaas checkout> also re-derives
#      the fixtures byte-identically from the real receipt blobs.
#   7. release court + root receipt (0.4.0, gates 095/097): in a copy of this pack made a real
#      git repository, consumer-v26.9.23 renders its court script before any observation, and
#      both receipts typed PARTIAL_ALIVE -> PARTIAL_ALIVE with subject @UNOBSERVED (ROOT.json
#      broken_term R_missing_identity, refused by the fleet validator), never omitted; the court
#      re-hashes the imports, runs the probes and gates (exit 0), writes its observation, including
#      the er:observedCourtInput set naming the whole court input (court, components, imports,
#      probes, gates), and removes the two receipts of the superseded observation; the re-sync
#      writes the root receipt (standing ALIVE,
#      subject = the repository HEAD, fleet validator ADMITTED, chatman receipt schema valid,
#      IMPORTS.sha256 rechecked), a further sync writes nothing and a fresh render from an empty
#      out/ reproduces every file; the committed observed.ttl is reproduced except for its
#      subject line, and its subject's pack tree equals the current one (the observation is of
#      the current law); a refused gate exits with its order and renders a BLOCKED
#      receipt; a gate command with a shell syntax error is that gate's refusal (exit = its order,
#      observed exit 2) while a command full of single quotes runs verbatim; a missing court root
#      exits 103; an observation missing a gate exit renders PARTIAL_ALIVE with broken_term
#      R_missing_consequence; a standing before of ALIVE stays ALIVE only with every gate observed
#      exit 0 and otherwise renders BLOCKED (R_missing_consequence / R_missing_identity), and a
#      pack copy without that construct clause renders ALIVE without evidence (anti-vacuity);
#      an import tamper exits 100 and a probe failure 101, both leaving the
#      observation untouched; a hand-edited court script or receipt is refused
#      (FM-WRITE-005); every row of court-mutants.EXPECTED.tsv is refused natively
#      (FM-PACK-013 at the named gate) and by the runner with the named reason, and admitted
#      by the runner once that gate is removed; rows C13-C19 are consumer triples that try to
#      extend the transition or failure-class law, and pack-ontology copies that drift from
#      the gates' closed tables; rows C20-C27 edit the court input after the committed
#      observation (import digest or path, court root, component SHA, an added gate, a withdrawn
#      import, the version) or drop its court-input set, so the stale observation must be refused
#      (rows marked `none` in the 7th column run without the committed observation); rows
#      C28-C35 witness each release-law gate 010-060 and 085 on this consumer (C29, C34 and C35:
#      FILTER-only UNION branches that ggen admitted natively before each branch bound its own
#      subject). The rows run concurrently (QUALIFY_JOBS, default 8).
#      7j: every gates/*.rq must be the only refusing gate of at least one passing mutant (step 5,
#      6e or 7g), so no gate is admission_vacuous.
#      CHATMAN_ECOSYSTEM_BIN=<ecosystem binary>, or CHATMAN_REPO=<git clone of chatman-ecosystem>
#      (qualify builds the committed qualification/chatman-harness against ecosystem-core extracted
#      from c59596f5 with git archive, cargo --offline), also seals the rendered receipt with
#      chatman-ecosystem's own receipt law and runs gate 097 against chatman's Standing::permits
#      on all 25 pairs of the five receipt standings.
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

# 5 (each graph mutant is also run through the runner without its named gate: it is admitted
#   exactly when no other gate refused it, and each admitted one is a sole-refusal witness for 7j)
WIT="$W/witness.tsv"; : > "$WIT"
gates_without() { # <gate file name> -> a gates dir without it (made once)
  if [ ! -d "$W/gates-no-$1" ]; then cp -R "$P/gates" "$W/gates-no-$1"; rm "$W/gates-no-$1/$1"; fi
  printf '%s\n' "$W/gates-no-$1"
}
while IFS=$'\t' read -r name code gate want reason; do
  case "$name" in ''|'#'*) continue ;; esac
  stage "$P/qualification/mutants/$name" "$W/m-$name" keep-out
  (cd "$W/m-$name" && "$GGEN" sync run > "$W/m-$name.json" 2> "$W/m-$name.err" < /dev/null); r=$?
  runner "$W/m-$name" "$W/m-$name.runner.log"; g=$?
  verdict=ok; also=""; rv=-
  [ "$r" -ne 0 ] && grep -q "\[$code\]" "$W/m-$name.err" || verdict=no
  if [ "$gate" != "-" ]; then grep -q "gate \`$gate\`" "$W/m-$name.err" || verdict=no; fi
  if [ "$want" = REFUSED ]; then
    [ "$g" -ne 0 ] && grep -q -- "$reason" "$W/m-$name.runner.log" || verdict=no
    also=$(awk -v g="$gate" '$1 == "GATE_VIOLATION" && $2 != g {print $2}' "$W/m-$name.runner.log" | tr '\n' ' ' | sed 's/ $//')
    python3 "$P/bin/run-gates.py" "$W/m-$name/release.ttl" "$(gates_without "$gate")" > "$W/m-$name.without-gate.log" 2>&1; rv=$?
    if [ -z "$also" ]; then
      if [ "$rv" = 0 ] && [ "$verdict" = ok ]; then printf '%s\tmutants/%s\n' "$gate" "$name" >> "$WIT"; else verdict=no; fi
    else
      [ "$rv" != 0 ] || verdict=no   # still refused by the other gates named in $also
    fi
  else
    [ "$g" -eq 0 ] || verdict=no
  fi
  if [ "$verdict" = ok ]; then ok "$name native=$r[$code] runner=$g without-gate=$rv${also:+ (also refused by $also)}"
  else no "$name native=$r runner=$g without-gate=$rv (see $W/m-$name.*)"; fi
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
    printf '090_imported_crown.rq\timported-crown/%s\n' "$name" >> "$WIT"
    ok "crown mutant $name: $reason (rows=$got native=$n[FM-PACK-013 090] without-090=$rv)"
  else no "crown mutant $name: want $reason rows=$rows, got rows=$got native=$n without-090=$rv (see $W/m-crown-$name.*)"; fi
done < "$P/qualification/imported-crown.EXPECTED.tsv"

# 7. release court + root receipt (0.4.0, gates 095/097, templates release-court.sh,
#    typed-checks.txt, root-receipt.toml/json, imports.sha256)
C=qualification/consumer-v26.9.23
PREFIX_LINE='@prefix er: <http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#> .'
court_copy() { # <dest>: a copy of this pack with a fresh consumer-v26.9.23 (no render, no ggen state)
  cp -R "$P" "$1"
  rm -rf "$1/$C/out" "$1/$C/.ggen" "$1/$C/.ggen-v2" "$1/.git"
}
git_commit() { # deterministic commit of the whole copy (real git, fixed identity and clock)
  (cd "$1" && git init -q && git add -A \
    && GIT_AUTHOR_NAME=qualify GIT_AUTHOR_EMAIL=qualify@localhost GIT_COMMITTER_NAME=qualify \
       GIT_COMMITTER_EMAIL=qualify@localhost GIT_AUTHOR_DATE=2026-09-23T00:00:00Z \
       GIT_COMMITTER_DATE=2026-09-23T00:00:00Z git commit -q -m "qualify court subject")
}
court() { # <copy> <log> [env...]: run the rendered court with COURT_OBSERVED=observed.ttl; echo exit
  local d=$1 log=$2; shift 2
  (cd "$d/$C" && env "$@" COURT_OBSERVED=observed.ttl bash out/scripts/crown_v26_9_23.sh > "$log" 2>&1); echo $?
}
sync_c() { (cd "$1/$C" && "$GGEN" sync run > "$2.json" 2> "$2.err"); }
# 7a positive: sync (no observation) -> court -> sync -> receipts
E="$W/court"; court_copy "$E"; printf '%s\n' "$PREFIX_LINE" > "$E/$C/observed.ttl"; git_commit "$E"
HEAD_SHA=$(git -C "$E" rev-parse HEAD)
if sync_c "$E" "$W/court-s1" && [ -s "$E/$C/out/scripts/crown_v26_9_23.sh" ] && [ -s "$E/$C/out/typed-checks.txt" ] \
   && [ -s "$E/$C/out/receipts/IMPORTS.sha256" ] \
   && ! python3 ~/.claude/dfcm/validate_receipt.py "$E/$C/out/receipts/ROOT.json" > "$W/court-s1-validate.log" 2>&1 \
   && grep -q "identity/subject_sha: 'UNOBSERVED' does not match" "$W/court-s1-validate.log" \
   && python3 - "$E/$C" "$P/qualification/chatman-receipt.schema.json" <<'PY'
import json, sys, tomllib
from pathlib import Path
import jsonschema
root = Path(sys.argv[1])
toml = tomllib.loads((root / "out/receipts/root-receipt.unsealed.toml").read_text())
jsonschema.validate(toml, json.load(open(sys.argv[2])))
assert (toml["standing_before"], toml["standing_after"]) == ("PARTIAL_ALIVE", "PARTIAL_ALIVE"), toml["standing_after"]
assert toml["subject"].endswith("@UNOBSERVED") and "subject_sha=UNOBSERVED" in toml["observed"]
assert toml["executed"] == ["gate 1 explicit-runner: UNOBSERVED", "gate 2 imports-recheck: UNOBSERVED", "gate 3 crosswalk-total: UNOBSERVED"]
r = json.loads((root / "out/receipts/ROOT.json").read_text())
assert r["standing"]["value"] == "PARTIAL_ALIVE" and r["standing"]["broken_term"] == "R_missing_identity", r["standing"]
assert r["identity"]["subject_sha"] == "UNOBSERVED" and [c["exit"] for c in r["replay"]["commands"]] == [-1, -1, -1]
PY
then
  ok "court sync before observation: script, typed checks, IMPORTS.sha256 and both receipts rendered; receipts typed PARTIAL_ALIVE -> PARTIAL_ALIVE @UNOBSERVED (R_missing_identity; the fleet validator refuses the missing subject)"
else no "court sync 1 (see $W/court-s1.* $W/court-s1-validate.log)"; fi
r=$(court "$E" "$W/court-run.log")
if [ "$r" = 0 ] && grep -q '^COURT_ALIVE ' "$W/court-run.log" && grep -q "er:observedOutput \"$HEAD_SHA\"" "$E/$C/observed.ttl" \
   && [ "$(grep -c 'er:observedExit 0 ; er:observedCommandSha256 "[0-9a-f]\{64\}" \.$' "$E/$C/observed.ttl")" = 3 ] \
   && [ "$(grep -c '^COURT_RECEIPT_SUPERSEDED ' "$W/court-run.log")" = 2 ] \
   && [ ! -e "$E/$C/out/receipts/ROOT.json" ] && [ ! -e "$E/$C/out/receipts/root-receipt.unsealed.toml" ] && [ -s "$E/$C/out/receipts/IMPORTS.sha256" ]; then
  ok "court exit 0 at $HEAD_SHA: 3 imports rehashed, 5 probes, 3 gates exit 0, observation written, the 2 receipts of the superseded observation removed"
else no "court run exit $r (see $W/court-run.log)"; fi
if python3 - "$E/$C/observed.ttl" > "$W/court-input.log" 2>&1 <<'PY'
import sys
from rdflib import Graph, URIRef
g = Graph().parse(sys.argv[1], format="turtle")
p = URIRef("http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#observedCourtInput")
subjects = set(g.subjects(p, None))
assert [str(s) for s in subjects] == ["https://ggen.dev/marketplace/qualification/chatman-ecosystem-release/v26.9.23/release"], subjects
kinds = sorted(str(o).split("|", 1)[0] for o in g.objects(None, p))
assert {k: kinds.count(k) for k in kinds} == {"component": 2, "court": 1, "gate": 3, "import": 3, "probe": 5}, kinds
assert "court|26.9.23|." in {str(o) for o in g.objects(None, p)}
print("court input:", len(kinds), "elements")
PY
then ok "observation names the whole court input on the release (1 court, 2 components, 3 imports, 5 probes, 3 gates)"; else no "observed court input (see $W/court-input.log)"; fi
if sync_c "$E" "$W/court-s2" && cp -R "$E/$C/out" "$W/court-out2" && sync_c "$E" "$W/court-s3" && diff -r "$E/$C/out" "$W/court-out2" > /dev/null \
   && python3 - "$W/court-s2.json" "$W/court-s3.json" <<'PY'
import json, sys
s2, s3 = (json.load(open(p)) for p in sys.argv[1:])
wrote = {w if isinstance(w, str) else json.dumps(w) for w in s2["written"]}
for want in ("out/receipts/root-receipt.unsealed.toml", "out/receipts/ROOT.json"):
    assert any(want in w for w in wrote), (want, s2["written"])
assert not s3["written"], s3["written"]
PY
then ok "receipts written by the sync after observation; a further sync writes nothing (byte-identical)"; else no "court sync 2/3 (see $W/court-s2.* $W/court-s3.*)"; fi
F="$W/court-fresh"; cp -R "$E" "$F"; rm -rf "$F/$C/out" "$F/$C/.ggen" "$F/$C/.ggen-v2"
if sync_c "$F" "$W/court-fresh" && diff -r "$E/$C/out" "$F/$C/out" > "$W/court-fresh.diff" 2>&1; then
  ok "fresh render from an empty out/ reproduces every rendered file byte-identically"; else no "fresh render differs (see $W/court-fresh.diff $W/court-fresh.*)"; fi
if python3 ~/.claude/dfcm/validate_receipt.py "$E/$C/out/receipts/ROOT.json" > "$W/court-root-validate.log" 2>&1 \
   && (cd "$E/$C" && shasum -a 256 -c --strict out/receipts/IMPORTS.sha256 > "$W/court-imports.log" 2>&1) \
   && python3 - "$E/$C" "$P/qualification/chatman-receipt.schema.json" "$HEAD_SHA" <<'PY'
import json, sys, tomllib
from pathlib import Path
import jsonschema
root, schema, head = Path(sys.argv[1]), json.load(open(sys.argv[2])), sys.argv[3]
toml = tomllib.loads((root / "out/receipts/root-receipt.unsealed.toml").read_text())
jsonschema.validate(toml, schema)
assert (toml["standing_before"], toml["standing_after"], toml["digest"]) == ("PARTIAL_ALIVE", "ALIVE", "")
assert toml["subject"].endswith("@" + head) and f"subject_sha={head}" in toml["observed"]
assert toml["executed"] == ["gate 1 explicit-runner: exit 0", "gate 2 imports-recheck: exit 0", "gate 3 crosswalk-total: exit 0"]
assert len(toml["replay"]) == 3 and len(toml["verified"]) == 3
assert "check:Dependency license and source policy=SUCCESSOR failure_class=pre_existing" in toml["excluded"]
root_json = json.loads((root / "out/receipts/ROOT.json").read_text())
assert root_json["identity"]["subject_sha"] == head and root_json["standing"]["value"] == "ALIVE"
assert [c["exit"] for c in root_json["replay"]["commands"]] == [0, 0, 0] and "broken_term" not in root_json["standing"]
assert (root / "out/typed-checks.txt").read_text() == "Dependency license and source policy\n"
print("receipt: PARTIAL_ALIVE -> ALIVE at", head, "; chatman schema valid; 3 imports; 1 typed check")
PY
then ok "root receipt contents (fleet ADMITTED, chatman schema, subject = HEAD, imports recheck)"; else no "root receipt contents (see $W/court-root-validate.log $W/court-imports.log)"; fi
# 7b the committed observation is the court's own output (all lines but the subject)
if diff <(grep -v '/probe-subject> ' "$P/$C/observed.ttl") <(grep -v '/probe-subject> ' "$E/$C/observed.ttl") > "$W/court-observed.diff"; then
  ok "committed observed.ttl reproduced by the court (subject line excluded)"; else no "committed observed.ttl differs from a fresh court observation (see $W/court-observed.diff)"; fi
CSUB=$(sed -n 's#.*/probe-subject> er:observedOutput "\([0-9a-f]\{40\}\)" ; .*#\1#p' "$P/$C/observed.ttl")
if [ -z "$CSUB" ]; then no "committed observed.ttl has no 40-hex subject"
elif git -C "$P" rev-parse --git-dir > /dev/null 2>&1; then
  if git -C "$P" merge-base --is-ancestor "$CSUB" HEAD 2> /dev/null; then ok "committed observation subject $CSUB is an ancestor of HEAD"; else no "committed observation subject $CSUB is not an ancestor of HEAD"; fi
  if git -C "$P" diff --quiet "$CSUB" -- . ":(exclude)$C/observed.ttl" 2> "$W/court-law-current.err"; then
    ok "committed observation is of the current pack law (pack tree at $CSUB = working tree, observed.ttl aside)"
  else git -C "$P" diff --stat "$CSUB" -- . ":(exclude)$C/observed.ttl" > "$W/court-law-current.diff" 2>&1
    no "pack changed since the observed subject $CSUB: re-run the court and commit its observation (see $W/court-law-current.diff)"; fi
else echo "SKIP committed observation subject ancestry: $P is not in a git checkout"; fi
# 7c a refused gate: exit = its er:gateOrder, observation carries the exit, receipt BLOCKED
B="$W/court-blocked"; court_copy "$B"; printf '%s\n' "$PREFIX_LINE" > "$B/$C/observed.ttl"
cat >> "$B/$C/release.ttl" <<'TTL'

q23:release er:gate q23:gate-witness-refusal .
q23:gate-witness-refusal a er:Gate ; er:gateOrder 4 ; er:gateName "witness-refusal" ; er:command "exit 7" .
TTL
git_commit "$B"; sync_c "$B" "$W/blocked-s1"
r=$(court "$B" "$W/blocked-run.log")
if [ "$r" = 4 ] && grep -q 'COURT_GATE_REFUSED order=4 name=witness-refusal exit=7' "$W/blocked-run.log" && grep -q 'gate-witness-refusal> er:observedExit 7 ;' "$B/$C/observed.ttl" \
   && sync_c "$B" "$W/blocked-s2" && python3 ~/.claude/dfcm/validate_receipt.py "$B/$C/out/receipts/ROOT.json" > "$W/blocked-validate.log" 2>&1 \
   && python3 - "$B/$C" <<'PY'
import json, sys, tomllib
from pathlib import Path
root = Path(sys.argv[1])
toml = tomllib.loads((root / "out/receipts/root-receipt.unsealed.toml").read_text())
assert (toml["standing_before"], toml["standing_after"]) == ("PARTIAL_ALIVE", "BLOCKED"), toml["standing_after"]
assert toml["executed"][-1] == "gate 4 witness-refusal: exit 7"
r = json.loads((root / "out/receipts/ROOT.json").read_text())
assert r["standing"]["value"] == "BLOCKED" and r["standing"]["broken_term"] == "mu_on_O"
assert [c["exit"] for c in r["replay"]["commands"]] == [0, 0, 0, 7]
PY
then ok "refused gate: court exit 4 (typed), observed exit 7, receipt PARTIAL_ALIVE -> BLOCKED (mu_on_O), fleet ADMITTED"; else no "blocked witness exit $r (see $W/blocked-*)"; fi
# 7c2 a gate command with a shell syntax error is that gate's own refusal (exit = its order, observed
#     exit 2), never a parse error of the court script; a command full of single quotes runs verbatim
X="$W/court-syntax"; court_copy "$X"; printf '%s\n' "$PREFIX_LINE" > "$X/$C/observed.ttl"
cat >> "$X/$C/release.ttl" <<'TTL'

q23:release er:gate q23:gate-witness-quotes , q23:gate-witness-syntax .
q23:gate-witness-quotes a er:Gate ; er:gateOrder 4 ; er:gateName "witness-quotes" ;
    er:command """v='a'\\''b' ; test "$v" = "a'b" && test "$(printf '%s' "it's")" = "it's" && echo 'kept: $HOME `x`' """ .
q23:gate-witness-syntax a er:Gate ; er:gateOrder 5 ; er:gateName "witness-syntax" ; er:command "if then fi" .
TTL
git_commit "$X"; sync_c "$X" "$W/syntax-s1"
r=$(court "$X" "$W/syntax-run.log")
if [ "$r" = 5 ] && grep -q 'COURT_GATE_PASS order=4 name=witness-quotes' "$W/syntax-run.log" && grep -qF 'kept: $HOME `x`' "$W/syntax-run.log" \
   && grep -q 'COURT_GATE_REFUSED order=5 name=witness-syntax exit=2' "$W/syntax-run.log" \
   && grep -q 'gate-witness-syntax> er:observedExit 2 ;' "$X/$C/observed.ttl" && grep -q 'gate-witness-quotes> er:observedExit 0 ;' "$X/$C/observed.ttl"; then
  ok "syntax error in a gate command: court exit 5 (its order), observed exit 2; single-quoted command ran verbatim"; else no "syntax witness exit $r (see $W/syntax-run.log)"; fi
# 7c3 a court root that is not a directory: exit 103 before any import, probe or gate; observation untouched
Z="$W/court-noroot"; court_copy "$Z"; printf '%s\n' "$PREFIX_LINE" > "$Z/$C/observed.ttl"
printf '\nq23:release er:courtRoot "no-such-dir" .\n' >> "$Z/$C/release.ttl"
sync_c "$Z" "$W/noroot-s1"; cp "$Z/$C/observed.ttl" "$W/noroot-observed.before"
r=$(court "$Z" "$W/noroot-run.log")
if [ "$r" = 103 ] && grep -q 'COURT_ROOT_MISSING court_root=no-such-dir' "$W/noroot-run.log" && ! grep -q 'COURT_IMPORT_OK' "$W/noroot-run.log" \
   && cmp -s "$Z/$C/observed.ttl" "$W/noroot-observed.before"; then
  ok "missing court root: court exit 103 (typed), observation untouched"; else no "missing court root exit $r (see $W/noroot-run.log)"; fi
# 7c4 an observation without one gate's exit (court input intact): PARTIAL_ALIVE kept, typed R_missing_consequence
Q="$W/court-partial"; cp -R "$E" "$Q"; rm -rf "$Q/$C/out" "$Q/$C/.ggen" "$Q/$C/.ggen-v2"
grep -v '/gate-crosswalk-total> er:observedExit ' "$E/$C/observed.ttl" > "$Q/$C/observed.ttl"
if sync_c "$Q" "$W/partial-s1" && python3 ~/.claude/dfcm/validate_receipt.py "$Q/$C/out/receipts/ROOT.json" > "$W/partial-validate.log" 2>&1 \
   && python3 - "$Q/$C" <<'PY'
import json, sys, tomllib
from pathlib import Path
root = Path(sys.argv[1])
toml = tomllib.loads((root / "out/receipts/root-receipt.unsealed.toml").read_text())
assert (toml["standing_before"], toml["standing_after"]) == ("PARTIAL_ALIVE", "PARTIAL_ALIVE"), toml["standing_after"]
assert toml["executed"][-1] == "gate 3 crosswalk-total: UNOBSERVED"
r = json.loads((root / "out/receipts/ROOT.json").read_text())
assert r["standing"]["value"] == "PARTIAL_ALIVE" and r["standing"]["broken_term"] == "R_missing_consequence"
assert [c["exit"] for c in r["replay"]["commands"]] == [0, 0, -1]
PY
then ok "unobserved gate: receipt PARTIAL_ALIVE -> PARTIAL_ALIVE, ROOT.json broken_term R_missing_consequence, fleet ADMITTED"; else no "partial witness (see $W/partial-*)"; fi
# 7c5 ALIVE only with complete evidence: a release whose standing before is ALIVE keeps ALIVE only
#     when every gate observed exit 0; with an incomplete or no observation it renders BLOCKED (the
#     only other transition chatman Standing::permits allows from ALIVE), typed by broken_term.
#     The same witness on a copy of the pack whose construct lacks that clause renders
#     ALIVE -> ALIVE without evidence (the clause is what the witness measures).
alive_before() { # <copy> <observation: full|partial|none> <label>
  local d=$1
  cp -R "$E" "$d"; rm -rf "$d/$C/out" "$d/$C/.ggen" "$d/$C/.ggen-v2"
  sed -i.bak 's/er:standingBefore er:PARTIAL_ALIVE ;/er:standingBefore er:ALIVE ;/' "$d/$C/release.ttl" && rm "$d/$C/release.ttl.bak"
  case $2 in
    partial) grep -v '/gate-crosswalk-total> er:observedExit ' "$E/$C/observed.ttl" > "$d/$C/observed.ttl" ;;
    none) printf '%s\n' "$PREFIX_LINE" > "$d/$C/observed.ttl" ;;
  esac
  sync_c "$d" "$3" && python3 - "$d/$C" <<'PY'
import json, sys, tomllib
from pathlib import Path
root = Path(sys.argv[1])
t = tomllib.loads((root / "out/receipts/root-receipt.unsealed.toml").read_text())
r = json.loads((root / "out/receipts/ROOT.json").read_text())
print(t["standing_before"], t["standing_after"], r["standing"]["value"], r["standing"].get("broken_term", "-"))
PY
}
A1=$(alive_before "$W/alive-full" full "$W/alive-full-s1"); A2=$(alive_before "$W/alive-partial" partial "$W/alive-partial-s1")
A3=$(alive_before "$W/alive-none" none "$W/alive-none-s1")
if [ "$A1" = "ALIVE ALIVE ALIVE -" ] && [ "$A2" = "ALIVE BLOCKED BLOCKED R_missing_consequence" ] && [ "$A3" = "ALIVE BLOCKED BLOCKED R_missing_identity" ] \
   && python3 ~/.claude/dfcm/validate_receipt.py "$W/alive-partial/$C/out/receipts/ROOT.json" > "$W/alive-partial-validate.log" 2>&1; then
  ok "standing before ALIVE: complete observation ALIVE -> ALIVE; one gate unobserved ALIVE -> BLOCKED (R_missing_consequence, fleet ADMITTED); no observation ALIVE -> BLOCKED (R_missing_identity)"
else no "ALIVE-before witness: full=[$A1] partial=[$A2] none=[$A3] (see $W/alive-*)"; fi
cp -R "$P" "$W/pack-no-alive-clause"; rm -rf "$W/pack-no-alive-clause/.git"
python3 - "$W/pack-no-alive-clause/templates/root-receipt.toml.tmpl" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
old = "IF(?before = er:ALIVE, er:BLOCKED, ?before)"
assert s.count(old) == 1, s.count(old)
open(p, "w").write(s.replace(old, "?before"))
PY
cp -R "$W/alive-none" "$W/alive-none-mutant"; rm -rf "$W/alive-none-mutant/$C/out" "$W/alive-none-mutant/$C/.ggen" "$W/alive-none-mutant/$C/.ggen-v2"
python3 - "$W/alive-none-mutant/$C/ggen.toml" "$W/pack-no-alive-clause" <<'PY'
import re, sys
path, pack = sys.argv[1], sys.argv[2]
text, n = re.subn(r'path = "[^"]+"', f'path = "{pack}"', open(path).read())
assert n == 1, n
open(path, "w").write(text)
PY
if sync_c "$W/alive-none-mutant" "$W/alive-none-mutant-s1" && grep -qx 'standing_after = "ALIVE"' "$W/alive-none-mutant/$C/out/receipts/root-receipt.unsealed.toml"; then
  ok "anti-vacuity: without the ALIVE clause the unobserved ALIVE-before receipt renders standing_after ALIVE (the witness above refuses exactly that)"
else no "ALIVE-clause mutant did not render ALIVE without evidence (see $W/alive-none-mutant-s1.*)"; fi
# 7d an imported file tampered after import: exit 100, observation untouched
T="$W/court-tamper"; cp -R "$E" "$T"; cp "$T/$C/observed.ttl" "$W/tamper-observed.before"
printf ' ' >> "$T/$C/imports/ce23-orders.ttl"
r=$(court "$T" "$W/tamper-run.log")
if [ "$r" = 100 ] && grep -q 'COURT_IMPORT_DIGEST_MISMATCH name=ce23-orders' "$W/tamper-run.log" && cmp -s "$T/$C/observed.ttl" "$W/tamper-observed.before" \
   && ! ls "$T/$C"/observed.ttl.partial.* > /dev/null 2>&1; then
  ok "import tamper: court exit 100 (typed), observation untouched"; else no "import tamper exit $r (see $W/tamper-run.log)"; fi
# 7e a probe that cannot observe (no git repository): exit 101, observation untouched
N="$W/court-nogit"; court_copy "$N"; cp "$P/$C/observed.ttl" "$W/nogit-observed.before"
sync_c "$N" "$W/nogit-s1"; r=$(court "$N" "$W/nogit-run.log" GIT_CEILING_DIRECTORIES="$W")
if [ "$r" = 101 ] && grep -q 'COURT_PROBE_FAILED name=subject_sha' "$W/nogit-run.log" && cmp -s "$N/$C/observed.ttl" "$W/nogit-observed.before"; then
  ok "probe failure: court exit 101 (typed), observation untouched"; else no "probe failure exit $r (see $W/nogit-run.log)"; fi
# 7f hand edits of a rendered court script or receipt are refused by the next sync (no force)
for f in scripts/crown_v26_9_23.sh receipts/root-receipt.unsealed.toml; do
  H="$W/court-hand-$(basename "$f")"; cp -R "$E" "$H"
  python3 - "$H/$C/out/$f" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("set -euo pipefail\n", "set -uo pipefail\n", 1) if p.endswith(".sh") else s.replace('standing_before = "PARTIAL_ALIVE"', 'standing_before = "UNKNOWN"', 1)
open(p, "w").write(s)
PY
  (cd "$H/$C" && "$GGEN" sync run > "$H.json" 2> "$H.err"); r=$?
  if [ "$r" != 0 ] && grep -q '\[FM-WRITE-005\]' "$H.err"; then ok "hand-edited out/$f refused by re-sync (FM-WRITE-005)"; else no "hand-edited out/$f survived re-sync (exit $r, see $H.err)"; fi
done
# 7g one-change graph mutants: refused natively and by the runner, admitted without the named gate;
#    the admitted witness row renders its crown into the receipt's verified[]
#    Rows run concurrently (QUALIFY_JOBS, default 8; each row is its own pack copy) and report in
#    table order; in columns 3 and 4 the two characters \n stand for a newline.
court_row() { # <name> <file> <old> <new> <gate> <reason> <observation>: writes $M.verdict (+ $M.witness)
  local name=$1 file=$2 old=$3 new=$4 gate=$5 reason=$6 obs=$7 M="$W/cm-$1" n g rv
  court_copy "$M"
  if [ "${obs:-committed}" = none ]; then printf '%s\n' "$PREFIX_LINE" > "$M/$C/observed.ttl"; fi
  if ! python3 - "$M/$C/$file" "$old" "$new" > "$M.edit" 2>&1 <<'PY'
import sys
path, old, new = sys.argv[1], sys.argv[2].replace("\\n", "\n"), sys.argv[3].replace("\\n", "\n")
s = open(path).read()
assert s.count(old) == 1, (path, old, s.count(old))
open(path, "w").write(s.replace(old, new))
PY
  then echo "FAIL court mutant $name: the old text is not exactly once in $file (see $M.edit)" > "$M.verdict"; return 0; fi
  (cd "$M/$C" && "$GGEN" sync run > "$M.json" 2> "$M.err"); n=$?
  python3 "$M/bin/run-gates.py" "$M/$C/release.ttl" "$M/gates" > "$M.runner" 2>&1; g=$?
  rv=-; if [ "$gate" != - ]; then rm "$M/gates/$gate"
  python3 "$M/bin/run-gates.py" "$M/$C/release.ttl" "$M/gates" > "$M.revert" 2>&1; rv=$?; fi
  if [ "$gate" = - ]; then
    if [ "$n" = 0 ] && [ "$g" = 0 ] && python3 - "$M/$C/out/receipts/root-receipt.unsealed.toml" "$reason" <<'PY'
import sys, tomllib
assert sys.argv[2] in tomllib.load(open(sys.argv[1], "rb"))["verified"]
PY
    then echo "PASS court witness $name admitted by both executors; receipt verified[] carries $reason" > "$M.verdict"
    else echo "FAIL court witness $name: native=$n runner=$g (see $M.*)" > "$M.verdict"; fi
    return 0
  fi
  if [ "$n" != 0 ] && grep -q '\[FM-PACK-013\]' "$M.err" && grep -q "gate \`$gate\`" "$M.err" \
     && [ "$g" != 0 ] && grep -qF -- "| $reason" "$M.runner" && [ "$rv" = 0 ]; then
    printf '%s\tcourt-mutants/%s\n' "$gate" "$name" > "$M.witness"
    echo "PASS court mutant $name: $reason (native=$n[FM-PACK-013 $gate] runner=$g without-gate=$rv)" > "$M.verdict"
  else echo "FAIL court mutant $name: want $gate/$reason, native=$n runner=$g without-gate=$rv (see $M.*)" > "$M.verdict"; fi
  return 0
}
court_rows=()
while IFS=$'\t' read -r name file old new gate reason obs; do
  case "$name" in ''|'#'*) continue ;; esac
  court_rows+=("$name")
  court_row "$name" "$file" "$old" "$new" "$gate" "$reason" "${obs:-}" < /dev/null &
  while [ "$(jobs -rp | wc -l)" -ge "${QUALIFY_JOBS:-8}" ]; do wait -n 2> /dev/null || wait; done
done < "$P/qualification/court-mutants.EXPECTED.tsv"
wait
for name in "${court_rows[@]}"; do
  v=$(cat "$W/cm-$name.verdict" 2> /dev/null || echo "FAIL court mutant $name: no verdict")
  case "$v" in PASS\ *) ok "${v#PASS }" ;; *) no "${v#FAIL }" ;; esac
  if [ -f "$W/cm-$name.witness" ]; then cat "$W/cm-$name.witness" >> "$WIT"; fi
done
# 7j no admission_vacuous gate: every gates/*.rq is the only refusing gate of at least one passing
#    mutant (step 5 or 7g: refused natively at that gate and by the runner, admitted by the runner
#    once that gate is removed; step 6e: gate 090 rows admitted without 090)
for rq in "$P"/gates/*.rq; do
  gn=$(basename "$rq")
  wits=$(awk -F'\t' -v g="$gn" '$1 == g {print $2}' "$WIT" | sort -u | tr '\n' ' ' | sed 's/ $//')
  if [ -n "$wits" ]; then ok "gate $gn witnessed as the sole refusing gate: $wits"
  else no "gate $gn has no mutant it alone refuses (admission_vacuous)"; fi
done
# 7h chatman-ecosystem's own receipt law (named skip without the binary). CHATMAN_REPO builds the committed
#    qualification/chatman-harness against ecosystem-core extracted from the exact law commit.
CHATMAN_LAW_SHA=c59596f5506e7a00ca4ed6b909ebf6d6659b74c1
if [ -z "${CHATMAN_ECOSYSTEM_BIN:-}" ] && [ -n "${CHATMAN_REPO:-}" ]; then
  HB="$W/chatman-harness-build"; mkdir -p "$HB"
  if git -C "$CHATMAN_REPO" archive "$CHATMAN_LAW_SHA" Cargo.toml Cargo.lock crates/ecosystem-core | tar -x -C "$HB" \
     && python3 - "$HB/Cargo.toml" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
text, n = re.subn(r'(?s)members = \[.*?\]\n(exclude = \[.*?\]\n)?', 'members = ["crates/ecosystem-core", "harness"]\n', text, count=1)
assert n == 1, n
open(path, "w").write(text)
PY
  then cp -R "$P/qualification/chatman-harness" "$HB/harness"
    if (cd "$HB" && rustc --version && cargo build --offline -p chatman-receipt-harness) > "$W/chatman-harness-build.log" 2>&1; then
      CHATMAN_ECOSYSTEM_BIN="${CARGO_TARGET_DIR:-$HB/target}/debug/chatman-receipt-harness"
      ok "chatman receipt harness built against ecosystem-core at $CHATMAN_LAW_SHA ($(head -1 "$W/chatman-harness-build.log"))"
    else no "chatman receipt harness build (see $W/chatman-harness-build.log)"; fi
  else no "chatman-ecosystem $CHATMAN_LAW_SHA not extractable from CHATMAN_REPO=$CHATMAN_REPO"; fi
fi
if [ -n "${CHATMAN_ECOSYSTEM_BIN:-}" ]; then
  K="$W/chatman-seal"; mkdir -p "$K/receipts"
  cp "$E/$C/out/receipts/root-receipt.unsealed.toml" "$K/receipts/release.toml"
  if (cd "$K" && "$CHATMAN_ECOSYSTEM_BIN" receipt seal > "$W/chatman-seal.log" 2>&1 && "$CHATMAN_ECOSYSTEM_BIN" receipt verify-all >> "$W/chatman-seal.log" 2>&1) \
     && grep -q 'RECEIPTS_SEALED count=1' "$W/chatman-seal.log" && grep -q 'RECEIPTS_ALIVE count=1' "$W/chatman-seal.log"; then
    ok "chatman ecosystem receipt seal + verify-all admit the rendered receipt (PARTIAL_ALIVE -> ALIVE)"; else no "chatman seal (see $W/chatman-seal.log)"; fi
  U="$W/chatman-unknown"; mkdir -p "$U/receipts"
  sed 's/^standing_before = "PARTIAL_ALIVE"$/standing_before = "UNKNOWN"/' "$E/$C/out/receipts/root-receipt.unsealed.toml" > "$U/receipts/release.toml"
  if (cd "$U" && "$CHATMAN_ECOSYSTEM_BIN" receipt seal > "$W/chatman-unknown.log" 2>&1); then no "chatman sealed an UNKNOWN -> ALIVE receipt"
  elif grep -q 'illegal receipt transition Unknown -> Alive' "$W/chatman-unknown.log"; then ok "chatman seal refuses the UNKNOWN -> ALIVE variant (the transition gate 097 refuses)"
  else no "chatman UNKNOWN variant refused for another reason (see $W/chatman-unknown.log)"; fi
  # 7i differential: gate 097's transition law against chatman's own Standing::permits over all 25
  #    pairs of the five receipt standings (gate executed by rdflib on the pack ontology plus one
  #    receipt with the pair asserted; chatman executed by sealing the rendered receipt with the pair)
  if python3 - "$P" "$E/$C/out/receipts/root-receipt.unsealed.toml" "$CHATMAN_ECOSYSTEM_BIN" "$W/chatman-diff" > "$W/chatman-diff.log" 2>&1 <<'PY'
import re, subprocess, sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, URIRef
pack, unsealed, binary, work = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
ER = Namespace("http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#")
names = ["UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "UNSUPPORTED"]
gate = (pack / "gates/097_root_receipt.rq").read_text()
text = unsealed.read_text()
permitted, mismatch = [], []
for b in names:
    for a in names:
        g = Graph(); g.parse(pack / "ontology.ttl", format="turtle")
        rr = URIRef("urn:qualify:receipt")
        g.add((rr, RDF.type, ER.RootReceipt)); g.add((rr, ER.standingBefore, ER[b])); g.add((rr, ER.standingAfter, ER[a]))
        gate_ok = not any(str(r[1]).startswith("illegal-standing-transition:") for r in g.query(gate))
        d = work / f"{b}-{a}" / "receipts"; d.mkdir(parents=True)
        body = re.sub(r'(?m)^standing_before = .*$', f'standing_before = "{b}"', text)
        body = re.sub(r'(?m)^standing_after = .*$', f'standing_after = "{a}"', body)
        (d / "release.toml").write_text(body)
        run = subprocess.run([binary, "receipt", "seal"], cwd=d.parent, capture_output=True, text=True)
        if run.returncode == 0: chatman_ok = True
        elif "illegal receipt transition" in run.stderr + run.stdout: chatman_ok = False
        else: raise SystemExit(f"{b}->{a}: chatman refused for another reason: {run.stderr.strip()}")
        print(f"{b}->{a} gate097={'permit' if gate_ok else 'refuse'} chatman={'permit' if chatman_ok else 'refuse'}")
        if gate_ok: permitted.append(f"{b}->{a}")
        if gate_ok != chatman_ok: mismatch.append(f"{b}->{a}")
assert not mismatch, mismatch
assert len(permitted) == 9 and "UNKNOWN->ALIVE" not in permitted, permitted
print("DIFFERENTIAL_AGREE pairs=25 permitted=9", " ".join(permitted))
PY
  then ok "gate 097 and chatman Standing::permits agree on all 25 standing pairs (9 permitted, UNKNOWN->ALIVE refused by both)"
  else no "gate 097 vs chatman Standing::permits differential (see $W/chatman-diff.log)"; fi
else echo "SKIP chatman receipt seal: set CHATMAN_REPO=<git clone of chatman-ecosystem> or CHATMAN_ECOSYSTEM_BIN=<ecosystem binary>"; fi

printf 'QUALIFICATION %s scratch=%s\n' "$([ $fail = 0 ] && echo ALIVE || echo REFUSED)" "$W"
exit $fail
