#!/bin/sh
# CE23 first-mile court (lane CE-INTAKE, wave CE0): re-derives every
# generated artifact of release/v26.9.23/sjira from its inputs and refuses on
# any drift. Run from any cwd; paths resolve from this script's location.
#
#   sh release/v26.9.23/sjira/compile_check.sh                  # check (default)
#   sh release/v26.9.23/sjira/compile_check.sh --write OUTROOT  # manufacture
#
# Check mode exits 0 iff, for each prose unit U in UNITS below:
#   1. corrections.py check: candidates/U.extract.json == apply(candidates/raw/U.extract.json,
#      candidates/corrections.json) (the recorded corrections of the LLM edge); the bench unit
#      carries no correction (its extraction is the raw edge byte for byte): every bench item is a
#      CE23-12 design obligation (chatman-ce23-12-standings.md BenchmarkDesign A = 'experiment,
#      DOE, corpus, statistics and qualification rules defined') and is never demoted off CE23-12;
#   2. prose_spans.py check --extract: candidates/U.ttl re-verifies against the
#      prose bytes of U (digest, spans, IRIs in the ce: namespace) and re-emits
#      byte-identically from the extraction (no hand edit); chatman-ce23 must
#      cover CE23-0 .. CE23-11;
#   3. unit_goal.py partition + check: the three units partition the 16
#      GoalCheckpoints under GC-CE-26.9.23 and units/U.goal.ttl is the
#      byte-identical projection of goal.ttl;
#   4. mix semantic_jira.compile_prose --check (ggen_igniter at GGEN_IGNITER_DIR)
#      recomputes compiled/U/{propositions,orders}.ttl byte-identically: SHACL
#      admission, contradiction/foreign-requirement/coverage rules (every gate of
#      the unit view is required, or REFUSED(uncovered_gate)), delta, conservation;
#   5. mix semantic_jira.compile_prose --admit-goal admits goal.ttl and each unit
#      view against the pack SHACL shapes (the GC23-3 goal-shapes court);
#   6. every GoalCheckpoint of goal.ttl names "sh release/v26.9.23/courts/<id>.sh",
#      each such script exists and is sh -n clean, and no other CE23-*.sh exists.
# --write OUTROOT runs step 4 without --check, writing OUTROOT/U/*.ttl (used to
# manufacture compiled/ and to prove two runs byte-identical).
#
# Every step runs under `env -i` with a fresh HOME and a PATH of only the pinned
# Erlang/Elixir bins, python3's and git's dirs, /usr/bin and /bin; it refuses
# (exit 75, UNKNOWN) when any of them holds a claude or zcode executable. No
# ANTHROPIC_/CLAUDE_/OPENAI_/ZAI_/GLM_/ZCODE_ variable reaches a step (only
# HOME, PATH, MIX_HOME, HEX_HOME, LANG, MIX_ENV, MIX_BUILD_PATH and
# PYTHONUSERBASE are set). mix runs
# with MIX_BUILD_PATH on a private APFS clone of $GGEN_IGNITER_DIR/_build/test,
# so the judged ggen_igniter checkout is read, never written.
#
# Env: GGEN_IGNITER_DIR (default /Users/sac/wt/v26922/fri/ggen_igniter-int),
#      PROSE_SPANS (default the frozen xaas-int scripts/sjira/prose_spans.py),
#      ELIXIR_BIN / ERLANG_BIN (default the .tool-versions pins 1.18.4-otp-27 / 27.2.4).
# Exit: 0 all hold; 1 refusal; 75 environment (tool missing / no no-LLM PATH).
set -u

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
rel=release/v26.9.23/sjira
gi=${GGEN_IGNITER_DIR:-/Users/sac/wt/v26922/fri/ggen_igniter-int}
spans=${PROSE_SPANS:-/Users/sac/wt/v26922/fri/xaas-int/scripts/sjira/prose_spans.py}
elixir_bin=${ELIXIR_BIN:-/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin}
erlang_bin=${ERLANG_BIN:-/Users/sac/.asdf/installs/erlang/27.2.4/bin}
ns="https://ggen-igniter.dev/sjira/chatman-26.9.23#"
UNITS="chatman-ce23 chatman-ce23-12-bench chatman-ce23-12-standings"

mode=check
out_root=""
if [ "${1:-}" = "--write" ]; then
  [ -n "${2:-}" ] || { echo "usage: compile_check.sh [--write OUTROOT]" >&2; exit 2; }
  mode=write
  out_root=$2
fi

unknown() {
  echo "UNKNOWN: compile_check: $*"
  exit 75
}

[ -f "$gi/mix.exs" ] || unknown "GGEN_IGNITER_DIR $gi is not a mix project"
[ -f "$gi/lib/mix/tasks/semantic_jira.compile_prose.ex" ] || unknown "$gi has no mix semantic_jira.compile_prose"
[ -f "$spans" ] || unknown "prose_spans.py not found at $spans"
[ -x "$elixir_bin/mix" ] || unknown "no mix in $elixir_bin"
[ -x "$erlang_bin/erl" ] || unknown "no erl in $erlang_bin"

path="$elixir_bin:$erlang_bin"
for tool in python3 git; do
  bin=$(command -v "$tool" 2>/dev/null) || unknown "$tool not on PATH"
  dir=$(dirname "$bin")
  case ":$path:" in *":$dir:"*) ;; *) path="$path:$dir" ;; esac
done
path="$path:/usr/bin:/bin"
# python3's user site (rdflib) is durable toolchain configuration, not a
# credential: its base is passed as PYTHONUSERBASE, as the xaas GC23 courts do.
pyuser=$(python3 -m site --user-base 2>/dev/null) || pyuser=""
old_ifs=$IFS
IFS=:
for dir in $path; do
  for llm in claude zcode; do
    [ -x "$dir/$llm" ] && { IFS=$old_ifs; unknown "$dir holds $llm; cannot build a no-LLM PATH"; }
  done
done
IFS=$old_ifs

scratch=$(mktemp -d "${TMPDIR:-/tmp}/ce23-compile-check.XXXXXX") || unknown "cannot create a scratch dir"
trap 'rm -rf "$scratch"' EXIT
trap 'exit 75' INT TERM
mkdir -p "$scratch/home"
if [ -d "$gi/_build/test" ]; then
  cp -cRp "$gi/_build/test" "$scratch/build-test" 2>/dev/null || {
    rm -rf "$scratch/build-test"
    cp -Rp "$gi/_build/test" "$scratch/build-test" || unknown "cannot clone $gi/_build/test"
  }
fi

# run <cmd...>: the no-LLM environment for every step.
run() {
  env -i \
    "HOME=$scratch/home" \
    "PATH=$path" \
    "MIX_HOME=${MIX_HOME:-$HOME/.mix}" \
    "HEX_HOME=${HEX_HOME:-$HOME/.hex}" \
    "LANG=${LANG:-en_US.UTF-8}" \
    "MIX_ENV=test" \
    "MIX_BUILD_PATH=$scratch/build-test" \
    ${pyuser:+"PYTHONUSERBASE=$pyuser"} \
    "$@"
}

fail=0
refuse() {
  echo "REFUSED: $*"
  fail=1
}

cd "$root" || unknown "cannot cd to $root"

if [ "$mode" = check ]; then
  run python3 "$here/corrections.py" check --raw-dir "$rel/candidates/raw" \
    --corrections "$rel/candidates/corrections.json" --out-dir "$rel/candidates" ||
    refuse "corrections.py check"
  run cmp -s "$rel/candidates/raw/chatman-ce23-12-bench.extract.json" \
    "$rel/candidates/chatman-ce23-12-bench.extract.json" ||
    refuse "chatman-ce23-12-bench carries a correction: bench items are CE23-12 design obligations (BenchmarkDesign/MSAContract), never demoted"

  for unit in $UNITS; do
    if [ "$unit" = chatman-ce23 ]; then
      gates="--require-gates 12 --gate-prefix CE23-"
    else
      gates=""
    fi
    # shellcheck disable=SC2086
    run python3 "$spans" check --source "$rel/$unit.md" --candidates "$rel/candidates/$unit.ttl" \
      --namespace "$ns" --prefix ce --extract "$rel/candidates/$unit.extract.json" $gates ||
      refuse "prose_spans.py check $unit"
  done

  run python3 "$here/unit_goal.py" partition --goal "$rel/goal.ttl" \
    --unit "$rel/chatman-ce23.md" --unit "$rel/chatman-ce23-12-bench.md" \
    --unit "$rel/chatman-ce23-12-standings.md" || refuse "unit_goal.py partition"
  for unit in $UNITS; do
    run python3 "$here/unit_goal.py" check --goal "$rel/goal.ttl" --unit "$rel/$unit.md" \
      --source "$rel/$unit.md" --out "$rel/units/$unit.goal.ttl" || refuse "unit_goal.py check $unit"
  done
fi

for unit in $UNITS; do
  if [ "$mode" = check ]; then
    out="$root/$rel/compiled/$unit"
    flag="--check"
  else
    out="$out_root/$unit"
    flag=""
    mkdir -p "$out" || unknown "cannot create $out"
  fi
  echo "== compile_prose $flag $unit"
  # shellcheck disable=SC2086
  run sh -c 'cd "$0" && exec mix semantic_jira.compile_prose "$@"' "$gi" \
    --source "$root/$rel/$unit.md" \
    --candidates "$root/$rel/candidates/$unit.ttl" \
    --goal "$root/$rel/units/$unit.goal.ttl" \
    --out-dir "$out" $flag || refuse "compile_prose $flag $unit"
done

if [ "$mode" = check ]; then
  for goal in "$rel/goal.ttl" "$rel/units/chatman-ce23.goal.ttl" "$rel/units/chatman-ce23-12-bench.goal.ttl" \
    "$rel/units/chatman-ce23-12-standings.goal.ttl"; do
    echo "== compile_prose --admit-goal $goal"
    run sh -c 'cd "$0" && exec mix semantic_jira.compile_prose --admit-goal --goal "$1"' "$gi" "$root/$goal" ||
      refuse "compile_prose --admit-goal $goal (pack SHACL shapes)"
  done

  commands=$(run python3 - "$rel/goal.ttl" <<'PY'
import sys
from rdflib import Graph, Namespace, RDF
SJ = Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
DCT = Namespace("http://purl.org/dc/terms/")
g = Graph()
g.parse(sys.argv[1], format="turtle")
for gate in sorted(g.subjects(RDF.type, SJ.GoalCheckpoint)):
    if g.value(gate, SJ.checkpointOf) is None:
        continue
    ident = str(g.value(gate, DCT.identifier))
    cmds = sorted(str(c) for c in g.objects(gate, SJ.courtCommand))
    print(ident + "\t" + ("|".join(cmds) if cmds else "-"))
PY
  ) || refuse "cannot read court commands from goal.ttl"
  n=0
  tab=$(printf '\t')
  while IFS=$tab read -r id cmd; do
    [ -n "$id" ] || continue
    want="sh release/v26.9.23/courts/$id.sh"
    if [ "$cmd" != "$want" ]; then
      refuse "gate $id court command is '$cmd', expected '$want'"
    elif [ ! -f "$root/release/v26.9.23/courts/$id.sh" ]; then
      refuse "missing court script release/v26.9.23/courts/$id.sh"
    elif ! sh -n "$root/release/v26.9.23/courts/$id.sh" 2>/dev/null; then
      refuse "court script release/v26.9.23/courts/$id.sh is not sh -n clean"
    fi
    n=$((n + 1))
  done <<EOF
$commands
EOF
  [ "$n" -eq 16 ] || refuse "goal.ttl has $n gates below the root (expected 16)"
  for script in "$root"/release/v26.9.23/courts/CE23-*.sh; do
    [ -e "$script" ] || continue
    id=$(basename "$script" .sh)
    printf '%s\n' "$commands" | awk -F '\t' -v g="$id" '$1 == g { found = 1 } END { exit !found }' ||
      refuse "court script $id.sh names no gate of goal.ttl"
  done
fi

if [ "$fail" -ne 0 ]; then
  echo "COMPILE_CHECK REFUSED"
  exit 1
fi
if [ "$mode" = check ]; then
  echo "COMPILE_CHECK OK: 3 units (chatman-ce23, chatman-ce23-12-bench, chatman-ce23-12-standings): corrections, candidates, unit views, compile_prose --check, goal admission and 16 gate courts all hold"
else
  echo "COMPILE_WRITE OK: $out_root/{chatman-ce23,chatman-ce23-12-bench,chatman-ce23-12-standings}"
fi
