#!/usr/bin/env bash
# Verification ladder for packs/scm-sigma-pack (PR-1 scope only).
# Cheapest-first: static parse -> SHACL -> generator determinism -> round-trip.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$ROOT/packs/scm-sigma-pack"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== 1. Static Turtle parse (ontology.ttl, shapes.ttl) =="
rapper -i turtle -o ntriples "$PACK/ontology.ttl" >/dev/null
rapper -i turtle -o ntriples "$PACK/shapes.ttl" >/dev/null
echo "OK: both files parse as valid Turtle"

echo "== 2. SHACL validation (shapes.ttl against ontology.ttl) =="
pyshacl -s "$PACK/shapes.ttl" -d "$PACK/ontology.ttl" -f human > "$TMP/shacl-report.txt" || {
  echo "SHACL VALIDATION FAILED:"
  cat "$TMP/shacl-report.txt"
  exit 1
}
grep -q "Conforms: True" "$TMP/shacl-report.txt" || {
  echo "SHACL report did not conform:"
  cat "$TMP/shacl-report.txt"
  exit 1
}
echo "OK: ontology.ttl conforms to shapes.ttl"

echo "== 3. Generator determinism (two independent runs must be byte-identical) =="
python3 "$PACK/templates/generate_sigma_schema.py" > "$TMP/sigma-a.json"
python3 "$PACK/templates/generate_sigma_schema.py" > "$TMP/sigma-b.json"
cmp "$TMP/sigma-a.json" "$TMP/sigma-b.json"
echo "OK: generator is deterministic"

echo "== 4. Projection round-trip (every ontology class appears in generated schema) =="
python3 - "$PACK/ontology.ttl" "$TMP/sigma-a.json" <<'PYEOF'
import sys, json, rdflib
RDF = rdflib.RDF
SIGMA = rdflib.Namespace("https://chatman.dev/scm/sigma#")
ontology_path, schema_path = sys.argv[1], sys.argv[2]
g = rdflib.Graph()
g.parse(ontology_path, format="turtle")
ontology_classes = {str(c).rsplit("#", 1)[-1] for c in g.subjects(RDF.type, SIGMA.Element)}
schema = json.load(open(schema_path))
schema_classes = set(schema["properties"].keys())
missing = ontology_classes - schema_classes
extra = schema_classes - ontology_classes
if missing:
    print(f"FAIL: classes in ontology but missing from generated schema: {sorted(missing)}")
    sys.exit(1)
if extra:
    print(f"FAIL: classes in generated schema but not in ontology (invented): {sorted(extra)}")
    sys.exit(1)
print(f"OK: {len(ontology_classes)} classes round-trip exactly between ontology.ttl and sigma.schema.json")
PYEOF

echo ""
echo "ALL CHECKS PASSED (PR-1 scope: ontology + one generated projection + validation)."
