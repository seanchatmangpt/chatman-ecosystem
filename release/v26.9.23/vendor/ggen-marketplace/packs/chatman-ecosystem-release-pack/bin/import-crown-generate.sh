#!/usr/bin/env bash
# Import an upstream checkpoint crown into a consumer and prove the committed projection.
# Precedent: packs/gym-autonomic-crown-pack/bin/crown-generate.sh (observe -> gates -> sync -> diff).
#
# READ-ONLY with respect to the consumer: everything is written into <workdir>, a staged copy
# of <consumer_dir>. Committing the lift or the render stays with the consumer's own lane.
#
# usage: import-crown-generate.sh <receipts_dir> <crown_sha> <paired_sha> <consumer_dir> <workdir> [crown_ttl]
#   crown_ttl: consumer-relative path of the lift, listed in the consumer's ggen.toml
#              (default imported/crown.ttl)
# 1. lift <receipts_dir> -> <workdir>/<crown_ttl>; when <consumer_dir>/<crown_ttl> is committed
#    it must be byte-identical (IMPORTED_CROWN_LIFT_DRIFT otherwise)
# 2. bin/run-gates.py over the consumer's union graph (explicit rdflib executor)
# 3. `ggen sync run` in <workdir> (native pack gates, FM-PACK-013; then render)
# 4. <workdir>/out/imported-crown.toml vs <consumer_dir>/out/imported-crown.toml
# exit 0 IMPORTED_CROWN_IDENTICAL_ALIVE; 1 refusal or drift; 3 nothing committed to compare
# (a first render proves nothing: commit the lift and the render, then rerun).
set -euo pipefail
PACK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
usage="usage: import-crown-generate.sh <receipts_dir> <crown_sha> <paired_sha> <consumer_dir> <workdir> [crown_ttl]"
RECEIPTS="${1:?$usage}"; CROWN_SHA="${2:?$usage}"; PAIRED_SHA="${3:?$usage}"
CONSUMER="$(cd "${4:?$usage}" && pwd)"; WORKDIR="${5:?$usage}"; CROWN_TTL="${6:-imported/crown.ttl}"
GGEN="${GGEN:-ggen}"

grep -q "\"$CROWN_TTL\"" "$CONSUMER/ggen.toml" || { echo "IMPORTED_CROWN_REFUSED $CROWN_TTL is not an input of $CONSUMER/ggen.toml"; exit 1; }
mkdir -p "$WORKDIR"
cp -R "$CONSUMER/." "$WORKDIR/"
rm -rf "$WORKDIR/.ggen" "$WORKDIR/.ggen-v2" "$WORKDIR/ggen.lock" "$WORKDIR/out"
# Path packs resolve against the original consumer dir, not the staged copy.
python3 - "$WORKDIR/ggen.toml" "$CONSUMER" <<'PY'
import os, re, sys
path, consumer = sys.argv[1], sys.argv[2]
text = open(path).read()
text = re.sub(r'path = "([^"]+)"', lambda m: f'path = "{os.path.normpath(os.path.join(consumer, m.group(1)))}"', text)
open(path, "w").write(text)
PY

mkdir -p "$(dirname "$WORKDIR/$CROWN_TTL")"
python3 "$PACK/bin/import-crown-lift.py" "$RECEIPTS" "$CROWN_SHA" "$PAIRED_SHA" > "$WORKDIR/$CROWN_TTL"
compared=0
if [[ -f "$CONSUMER/$CROWN_TTL" ]]; then
  cmp -s "$CONSUMER/$CROWN_TTL" "$WORKDIR/$CROWN_TTL" || { echo "IMPORTED_CROWN_LIFT_DRIFT $CONSUMER/$CROWN_TTL differs from the lift of $RECEIPTS"; exit 1; }
  compared=$((compared + 1))
fi

SOURCE="$(python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["ontology"]["source"])' "$WORKDIR/ggen.toml")"
python3 "$PACK/bin/run-gates.py" "$WORKDIR/$SOURCE" "$PACK/gates" > "$WORKDIR/run-gates.log" \
  || { cat "$WORKDIR/run-gates.log"; echo "IMPORTED_CROWN_REFUSED explicit runner"; exit 1; }
(cd "$WORKDIR" && "$GGEN" sync run --format json > "$WORKDIR/ggen-sync.json" 2> "$WORKDIR/ggen-sync.log") \
  || { grep -v ' INFO ' "$WORKDIR/ggen-sync.log" | tail -5; echo "IMPORTED_CROWN_REFUSED ggen sync run"; exit 1; }
echo "IMPORTED_CROWN_GENERATED $WORKDIR/out/imported-crown.toml"

if [[ -f "$CONSUMER/out/imported-crown.toml" ]]; then
  diff -u "$CONSUMER/out/imported-crown.toml" "$WORKDIR/out/imported-crown.toml" || { echo "IMPORTED_CROWN_RENDER_DRIFT"; exit 1; }
  compared=$((compared + 1))
fi
if [[ $compared -lt 2 ]]; then
  echo "IMPORTED_CROWN_UNCOMMITTED compared=$compared/2 (commit $CROWN_TTL and out/imported-crown.toml to arm the drift check)"
  exit 3
fi
echo "IMPORTED_CROWN_IDENTICAL_ALIVE"
