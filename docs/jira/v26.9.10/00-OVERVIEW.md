# v26.9.10 — BFCC: Buckminster Fuller Canon Compatibility

> **Standard, not homage.** BFCC does not mean "inspired by Fuller." It means the exact stated
> subject/revision can demonstrate compatibility with a defined subset of Fuller's canon —
> Comprehensive, Anticipatory, Design, Science, Generalized Principles, Synergy,
> Ephemeralization, Trimtab leverage, World/resource inventory, Integrity — via an explicit
> canon-to-engineering projection, a falsifiable invariant, and admissible evidence. See
> `docs/BFCC.md` (BFCC-005) for the full doctrine once written.

## Governing question

> What is the maximum increase in comprehensive verified capability obtainable from the
> minimum new canonical information, resources, and exceptional reasoning, while causing each
> solved problem to make its problem class cheaper to solve again?

## Why this ticket set exists

BFCC is proposed as three pieces of executable capital, not a documentation edit:

$$
\text{BFCC ontology} + \text{BFCC verifier} + \text{BFCC benchmark}
$$

This repo already has a working pattern for exactly this shape of thing —
`catalog/dfcm.toml` + `ontology/dfcm.ttl`/`.shacl.ttl` + `scripts/verify_dfcm_profile.py`,
`catalog/formal-discovery-loop.toml` + `scripts/verify_formal_discovery_loop.py`,
`catalog/frontier-release-factory.toml` + `scripts/verify_frontier_release_factory.py` — so
BFCC-001 through BFCC-006 below are scoped to extend that same family rather than invent a new
shape (BFCC's own W-gate: inventory before invention).

## Ticket sequence

| Ticket | Deliverable | Depends on |
|---|---|---|
| [BFCC-001](BFCC-001.md) | Ontology (`ontology/bfcc.ttl` + `.shacl.ttl`) | none |
| [BFCC-002](BFCC-002.md) | Catalog entry (`catalog/bfcc.toml`, 10 gates) | BFCC-001 |
| [BFCC-003](BFCC-003.md) | Verifier (`scripts/verify_bfcc.py` + tests) | BFCC-001, BFCC-002 |
| [BFCC-004](BFCC-004.md) | Ephemeralization benchmark (`scripts/bfcc_benchmark.py` + tests) | BFCC-003 |
| [BFCC-005](BFCC-005.md) | Doctrine doc + catalog registration (`docs/BFCC.md`) | BFCC-002 |
| [BFCC-006](BFCC-006.md) | CI conformance workflow | BFCC-003, BFCC-004 |
| [BFCC-007](BFCC-007.md) | v26.9.10 case study / working-backwards press release (HTN/FOND/HDDL episode) as the first real assessment subject | BFCC-001 – BFCC-006 |

## Standing vocabulary (closed set, used by every ticket below)

`BFCC-CANDIDATE`, `BFCC-PARTIAL`, `BFCC-BLOCKED`, `BFCC-UNKNOWN`, `BFCC-ALIVE`.
`BFCC-ALIVE` requires exact-subject verification — never inferred, never transferred from a
related or stale subject, never averaged from partial gate coverage. All tickets in this set
are currently `BFCC-CANDIDATE` (design specs, no implementation yet).

## Authority boundary (binds every ticket below)

BFCC assessment is `OBSERVE`/`VERIFY` only. Passing or failing a BFCC gate never grants `DO`
authority by itself — mirrors this repo's existing `[authority]` convention in `dfcm.toml`
(`hooks_grant_authority = false`, `plan_grants_authority = false`, `proof_grants_authority =
false`). A `BFCC-ALIVE` standing on a subject is not itself a release/merge/deploy decision.

## See Also

- `docs/architecture/dfcm-public-ontology-profile.md` — sibling conformance-profile doctrine
- `docs/FORMAL-DISCOVERY-FACTORY.md` — sibling conformance-profile doctrine, same catalog/
  verifier/test shape BFCC extends
- `docs/jira/v26.8.19/00-OVERVIEW.md` — prior release's ticket-set convention this set follows
