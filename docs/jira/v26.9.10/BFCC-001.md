# BFCC-001 — BFCC Ontology

Ticket Key: BFCC-001
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE

## Problem

BFCC needs a machine-readable vocabulary for its own ten gates (Comprehensive,
Anticipatory, Design, Science, Generalized Principles, Synergy, Ephemeralization,
Trimtab, World/inventory, Integrity), the canon-to-engineering projection each gate
carries, and the shape of a conformance receipt — before any verifier or benchmark can
be written against it. Without this, "BFCC-ALIVE" is prose, not a checkable claim.

## Customer/system need

`scripts/verify_bfcc.py` (BFCC-003) and any future SHACL-conformance check need a
canonical term set to validate structure against, the same way
`scripts/verify_dfcm_profile.py` validates `catalog/dfcm.toml` against
`ontology/dfcm.ttl` + `ontology/dfcm.shacl.ttl`.

## Current gap

No `ontology/bfcc.ttl` or `ontology/bfcc.shacl.ttl` exists. `catalog/bfcc.toml`
(BFCC-002) has nothing to validate its `[[gate]]` entries against.

## Scope

- `ontology/bfcc.ttl` — namespace `bfcc:` at
  `https://seanchatmangpt.github.io/chatman-ecosystem/ontology/bfcc#`. Thin remainder:
  reuse `earl:` (Evaluation and Report Language — direct fit for a conformance-report
  vocabulary), `prov:`, `pplan:`, `dcterms:`, `skos:`. New classes only for genuinely
  new concepts: `bfcc:Gate` (10 individuals, one per canon letter), `bfcc:CanonPrinciple`,
  `bfcc:EngineeringProjection`, `bfcc:FalsifierCriterion`, `bfcc:ConformanceReceipt`
  (`rdfs:subClassOf earl:Assertion`), `bfcc:ResourceVector`. New properties:
  `bfcc:projectsFrom` (Gate → CanonPrinciple — the structural enforcement of "our
  engineering practice ≠ Fuller said this"; a Gate individual without this edge is
  malformed), `bfcc:hasFalsifier`, `bfcc:ephemeralizationRatio`, `bfcc:trimtabLeverage`,
  `bfcc:synergyGain`.
- File-header prose states the two invariants the verifier will check literally:
  "compatibility is Boolean, never an averaged score" and "no standing transfers from a
  related or stale subject."
- `ontology/bfcc.shacl.ttl` — one `sh:NodeShape` per class. The `ConformanceReceipt`
  shape requires `subject`/`revision`/`standing`/`canonSources`/`gatesEvaluated`/
  `falsifierPerGate` with `sh:in` constraining `standing` to the closed BFCC standing
  vocabulary.

## Non-goals

- No SHACL execution engine wired into CI yet (that's a later, separate ticket if
  needed) — this ticket only produces the shapes file.
- No claim that any real subject is BFCC-compatible — this is vocabulary only.

## Dependencies

None. Pure-text RDF/Turtle, no runtime dependency.

## Risks

Namespace/prefix drift between this file and `catalog/bfcc.toml`'s future
`[public_ontologies]` table (BFCC-002) if the two aren't kept in sync — mitigated by
BFCC-003's verifier checking prefix correspondence, same pattern `verify_dfcm_profile.py`
already uses for `dfcm.toml` vs `dfcm.ttl`.

## Authority boundary

Pure vocabulary definition. `OBSERVE`/`VERIFY` only, no `DO` authority implied.

## Rollback

Delete both files; nothing else in the repo depends on them until BFCC-002/003 land.

## Acceptance commands

```
python3 -c "print('placeholder — real check below')"
# If rdflib is available:
python3 -c "import rdflib; g = rdflib.Graph(); g.parse('ontology/bfcc.ttl', format='turtle'); g.parse('ontology/bfcc.shacl.ttl', format='turtle'); print('parsed OK', len(g))"
# If rdflib is not available, at minimum:
grep -c "skos:definition" ontology/bfcc.ttl
grep -c "sh:targetClass" ontology/bfcc.shacl.ttl
```

## Observable Definition of Done

- Both files exist, parse as valid Turtle (verified with `rdflib` if installed, else a
  grep-level structural check — never claimed RDF-valid without actually parsing when
  `rdflib` is available).
- All 10 `bfcc:Gate` individuals present, each with a `bfcc:projectsFrom` edge to a
  `bfcc:CanonPrinciple` individual and a `skos:definition`.
- SHACL `sh:targetClass` set is a 1:1 match against the ontology's own class set (no
  orphan shape, no unshaped class).
- Exact-head CI is observed before any standing beyond `BFCC-CANDIDATE` is claimed.
