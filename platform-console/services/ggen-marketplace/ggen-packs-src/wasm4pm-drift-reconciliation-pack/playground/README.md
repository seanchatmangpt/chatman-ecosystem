# playground/

Real, read-only verifier for this pack's `DriftClaim` ontology. Runs each claim's real check
(`file_exists`/`file_absent`/`grep_pattern`/`command_output_matches`) against an actual
target repo and reports match/contradict — never writes to anything it checks.

## Usage

```bash
cd platform-console/services/ggen-marketplace/ggen-packs-src/wasm4pm-drift-reconciliation-pack
python3 playground/verify.py --repo ~/wasm4pm
```

Exits 0 if all claims match, 1 if any contradict (or errors) — usable as a real CI gate.

As of 2026-08-21, real run: `7 match, 0 contradict, 7 total` — confirming the 7 known doc/code
drift fixes made this session still hold on disk.

## Real gotcha found and fixed this pass

The gate (`gates/010_required.rq`) originally matched on the abstract `drc:DriftClaim` parent
class and silently returned 0 rows even for real instances — plain SPARQL (rdflib, and most
stores without an explicit RDFS-reasoning mode) does not infer `rdf:type` through
`rdfs:subClassOf`. Fixed to match on the two concrete subclasses
(`SourceContradictionClaim`/`FilesystemFactClaim`) directly. Confirmed via a deliberately broken
fixture: 4/4 expected missing-property rows now returned correctly.
