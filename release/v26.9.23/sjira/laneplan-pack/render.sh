#!/bin/sh
# Renders the CE23 lane plan (lane CE-LANEPLAN, wave F1ce) with stock
# `mix ggen_igniter.sync` (ggen_igniter at GGEN_IGNITER_DIR): one
# OUTDIR/wave-<id>.json per lp:Wave of registry.ttl, from ONE merged ontology
# (sync --ontology reads one file):
#
#   goal.ttl + compiled/*/orders.ttl + compiled/*/propositions.ttl
#   + laneplan-pack/{ontology,registry,routes,dependencies}.ttl
#
#   sh release/v26.9.23/sjira/laneplan-pack/render.sh OUTDIR            # merge + render
#   sh release/v26.9.23/sjira/laneplan-pack/render.sh OUTDIR MERGED.ttl # render a given graph
#   sh release/v26.9.23/sjira/laneplan-pack/render.sh --merge MERGED.ttl # only write the merge
#
# OUTDIR must not exist or be empty; it is also sync's --manifest-dir (the
# authorized output root; the reconciliation manifest lands in
# OUTDIR/.ggen_igniter), and --verify-cwd is the ggen_igniter checkout.
# A refusal (REFUSED:SJIRA_LANE_PLAN <reason>) raises inside the template,
# before sync actuates anything: no wave file is written.
#
# No-LLM environment (the compile_check.sh discipline): every mix/python step
# runs under env -i with a fresh HOME and a PATH of only the pinned
# Erlang/Elixir bins, python3's and git's dirs, /usr/bin and /bin; exit 75
# (UNKNOWN) when a dir on it holds a claude or zcode executable. mix runs with
# MIX_BUILD_PATH on a private APFS clone of $GGEN_IGNITER_DIR/_build/test
# (LANEPLAN_BUILD names an existing clone to reuse), so the judged ggen_igniter
# checkout is read, never written.
#
# Env: GGEN_IGNITER_DIR (default /Users/sac/wt/v26922/fri/ggen_igniter-int),
#      ELIXIR_BIN / ERLANG_BIN (default the .tool-versions pins 1.18.4-otp-27 /
#      27.2.4), LANEPLAN_BUILD (optional private MIX_BUILD_PATH clone).
# Exit: sync's exit code (0 rendered; 1 refused or failed); 2 usage; 75 environment.
set -u

here=$(cd "$(dirname "$0")" && pwd)
sjira=$(cd "$here/.." && pwd)
gi=${GGEN_IGNITER_DIR:-/Users/sac/wt/v26922/fri/ggen_igniter-int}
elixir_bin=${ELIXIR_BIN:-/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin}
erlang_bin=${ERLANG_BIN:-/Users/sac/.asdf/installs/erlang/27.2.4/bin}

unknown() {
  echo "UNKNOWN: laneplan render: $*"
  exit 75
}

merge() {
  # The order is fixed; the render depends only on the graph, not on it.
  cat "$sjira/goal.ttl" \
    "$sjira/compiled/chatman-ce23/orders.ttl" \
    "$sjira/compiled/chatman-ce23-12-bench/orders.ttl" \
    "$sjira/compiled/chatman-ce23-12-standings/orders.ttl" \
    "$sjira/compiled/chatman-ce23/propositions.ttl" \
    "$sjira/compiled/chatman-ce23-12-bench/propositions.ttl" \
    "$sjira/compiled/chatman-ce23-12-standings/propositions.ttl" \
    "$here/ontology.ttl" "$here/registry.ttl" "$here/routes.ttl" "$here/dependencies.ttl"
}

if [ "${1:-}" = "--merge" ]; then
  [ -n "${2:-}" ] || { echo "usage: render.sh --merge MERGED.ttl" >&2; exit 2; }
  merge > "$2" || unknown "cannot write $2"
  exit 0
fi

[ -n "${1:-}" ] || { echo "usage: render.sh OUTDIR [MERGED.ttl]" >&2; exit 2; }
out=$1
merged=${2:-}

[ -f "$gi/mix.exs" ] || unknown "GGEN_IGNITER_DIR $gi is not a mix project"
[ -f "$gi/lib/mix/tasks/ggen_igniter.sync.ex" ] || unknown "$gi has no mix ggen_igniter.sync"
[ -f "$gi/lib/ggen_igniter/semantic_jira/bootstrap/graph.ex" ] || unknown "$gi has no GgenIgniter.SemanticJira.Bootstrap.Graph (tuple_digest/1)"
[ -x "$elixir_bin/mix" ] || unknown "no mix in $elixir_bin"
[ -x "$erlang_bin/erl" ] || unknown "no erl in $erlang_bin"

path="$elixir_bin:$erlang_bin"
for tool in python3 git; do
  bin=$(command -v "$tool" 2>/dev/null) || unknown "$tool not on PATH"
  dir=$(dirname "$bin")
  case ":$path:" in *":$dir:"*) ;; *) path="$path:$dir" ;; esac
done
path="$path:/usr/bin:/bin"
old_ifs=$IFS
IFS=:
for dir in $path; do
  for llm in claude zcode; do
    [ -x "$dir/$llm" ] && { IFS=$old_ifs; unknown "$dir holds $llm; cannot build a no-LLM PATH"; }
  done
done
IFS=$old_ifs

if [ -e "$out" ] && [ -n "$(ls -A "$out" 2>/dev/null)" ]; then
  echo "laneplan render: OUTDIR $out is not empty" >&2
  exit 2
fi
mkdir -p "$out" || unknown "cannot create $out"
out=$(cd "$out" && pwd)

scratch=$(mktemp -d "${TMPDIR:-/tmp}/ce23-laneplan-render.XXXXXX") || unknown "cannot create a scratch dir"
trap 'rm -rf "$scratch"' EXIT
trap 'exit 75' INT TERM
mkdir -p "$scratch/home"
if [ -z "$merged" ]; then
  merged="$scratch/merged.ttl"
  merge > "$merged" || unknown "cannot merge the lane-plan inputs"
fi
[ -f "$merged" ] || unknown "no merged graph $merged"
merged=$(cd "$(dirname "$merged")" && pwd)/$(basename "$merged")

build=${LANEPLAN_BUILD:-}
if [ -z "$build" ]; then
  build="$scratch/build-test"
  if [ -d "$gi/_build/test" ]; then
    cp -cRp "$gi/_build/test" "$build" 2>/dev/null || {
      rm -rf "$build"
      cp -Rp "$gi/_build/test" "$build" || unknown "cannot clone $gi/_build/test"
    }
  fi
fi

q="$here/queries"
# shellcheck disable=SC2016
env -i \
  "HOME=$scratch/home" \
  "PATH=$path" \
  "MIX_HOME=${MIX_HOME:-$HOME/.mix}" \
  "HEX_HOME=${HEX_HOME:-$HOME/.hex}" \
  "LANG=${LANG:-en_US.UTF-8}" \
  "MIX_ENV=test" \
  "MIX_BUILD_PATH=$build" \
  sh -c 'cd "$0" && exec mix ggen_igniter.sync "$@"' "$gi" \
  --ontology "$merged" \
  --query "lanes=$q/lanes.rq" \
  --query "fields=$q/fields.rq" \
  --query "gates=$q/gates.rq" \
  --query "edges=$q/edges.rq" \
  --query "routes=$q/routes.rq" \
  --query "executors=$q/executors.rq" \
  --query "plan=$q/plan.rq" \
  --query "waves=$q/waves.rq" \
  --for-each waves \
  --template "$here/templates/lane_wave.json.eex" \
  --out "$out/wave-<%= wave_id %>.json" \
  --manifest-dir "$out" \
  --verify-cwd "$gi"
code=$?
exit "$code"
