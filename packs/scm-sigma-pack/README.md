# scm-sigma-pack

Canonical Sigma ontology for the Chatman Semantic Coordination Machine (SCM): the shared
vocabulary of semantic elements (Identity, Principal, Role, Topology, Relation, State,
Possibility, Observation, Projection, Time, Objective, Authority, Grant, Delegation,
Handoff, Continuation, Action, Consequence, Receipt, Standing) that every
jurisdiction-bound repo in the ecosystem composes rather than reinvents. Each class is
tagged with the Z-coordinate it belongs to (`Z=(P,Gamma,Omega,B,tau,J|A,R)`) and the
jurisdiction (repo role) permitted to emit or consume it.

**PR-1 of the 2026 backwards-chain: ontology only.** No composition operators, no
jurisdiction refusal contracts, no runtime verifier, and no end-to-end equivalence proof
are established by this pack — those are separate, later units of work (PR-2 through PR-5)
per the SCM 2030 press release backwards-chain.

## Provenance

- Landed with PR-1 "canonical Sigma ontology + generated projection + validation",
  initial commit `551cf5c`, dated 2026-09-12 (verified via `git log`).
- `ontology.ttl` is the HAND-AUTHORED source of truth. All downstream artifacts
  (JSON Schema, per-repo types, etc.) are generated from it, never hand-duplicated.

## Contents

| File | Size | What it is |
|---|---|---|
| `pack.toml` | 6,358 B | Pack identity: name `scm-sigma-pack`, **version `0.1.0`** (as of 2026-09-21 — version changes are pack-admission actions, not docs; do not bump in place), description |
| `ontology.ttl` | 6,358 B* | Canonical source. 120 triples, 20 `sigma:Element` classes, prefixes `sigma:` `<https://chatman.dev/scm/sigma#>`, `rdfs:`, `xsd:`. Invariants recorded here (enforced in later PRs, not here): `SELECT != CONSTRUCT != DO`, `HDDL/FOND subsetOf SELECT`, `PlannerOutput != Authority`, `DO => Receipt` |
| `shapes.ttl` | 1,211 B | 30 triples, **2 SHACL `sh:NodeShape`**: `sigma:ElementShape` (every Element must declare ≥1 `zCoordinate` from the 8-value enum and ≥1 `jurisdiction`) and `sigma:ReceiptClassShape` (Receipt must carry ≥1 jurisdiction; instance-level identity/authority/consequence/replay/standing properties are a forward pointer to PR-4, not yet constraints) |
| `sigma.schema.json` | 16,009 B | GENERATED projection (draft-07, `$id` `https://chatman.dev/scm/sigma.schema.json`), 20 classes. Do not hand-edit |
| `templates/generate_sigma_schema.py` | 3,062 B | The sole lawful path from `ontology.ttl` to `sigma.schema.json`. Deterministic: sorted class order, no timestamps, byte-identical output across runs |

\* `pack.toml` and `ontology.ttl` are both 6,358 bytes — a coincidence, not a relation.

Z-coordinate distribution of the 20 classes: P (Identity, Principal, Role), Gamma
(Topology, Relation), Omega (State, Possibility), B (Observation, Projection), tau (Time),
J (Objective), A (Authority, Grant, Delegation, Handoff, Continuation, Action,
Consequence), R (Receipt, Standing). Cross-coordinate classes: Handoff (A,P), Consequence
(A,B), Continuation (P,tau). Jurisdictions referenced: `ash_a2a`, `ggen-marketplace`,
`beam4pm`, `ash_r2rml`, `gitvan`, `autofde-lab`, `mfw`, `bcinr`, `gymact`, `ggen-ecosystem`.

## How to validate

From the repository root:

```bash
bash scripts/validate_sigma.sh
```

Four-step ladder (cheapest-first): (1) static Turtle parse of `ontology.ttl` + `shapes.ttl`
via `rapper`; (2) SHACL validation of `shapes.ttl` against `ontology.ttl` via `pyshacl`
(must report `Conforms: True`); (3) generator determinism — two independent runs of
`generate_sigma_schema.py` must be byte-identical; (4) projection round-trip — the class
sets of `ontology.ttl` and `sigma.schema.json` must match exactly, no missing, no invented.

**Observed result, as of 2026-09-21** (run from repo root, full output captured):

```
== 1. Static Turtle parse (ontology.ttl, shapes.ttl) ==
OK: both files parse as valid Turtle
== 2. SHACL validation (shapes.ttl against ontology.ttl) ==
OK: ontology.ttl conforms to shapes.ttl
== 3. Generator determinism (two independent runs must be byte-identical) ==
OK: generator is deterministic
== 4. Projection round-trip (every ontology class appears in generated schema) ==
OK: 20 classes round-trip exactly between ontology.ttl and sigma.schema.json

ALL CHECKS PASSED (PR-1 scope: ontology + one generated projection + validation).
```

Exit code: **0**.

## Status (as of 2026-09-21)

- Validator: **ALIVE** — observed execution this session, all four checks passed, exit 0.
- Everything else in this README (file sizes, triple/class/shape counts, provenance) is
  **inspection-only**, not execution evidence.

## Scope note

This pack is local-only: this repository has never been pushed to a remote, and any
GitHub repository with a similar name is unrelated to this working tree.
