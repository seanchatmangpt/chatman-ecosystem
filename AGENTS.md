# chatman-ecosystem

Program constitution / cross-repo semantic contract for the Semantic
Coordination Machine (SCM). This repo owns the canonical semantic
elements (Σ) and the cross-repo jurisdiction contract; it does not own
product/runtime implementation.

## The calculus

    Z = (P, Γ, Ω, B, τ, J | A, R)

    P = principals / identities / roles
    Γ = topology / relationships / communication / dependencies
    Ω = possibility space
    B = observed / believed / projected state
    J = objectives
    τ = temporal / causal state
    A = authority
    R = receipts / provenance / replay / standing

Load-bearing invariants:

- `SELECT != CONSTRUCT != DO`
- `HDDL/FOND ⊆ SELECT`
- `PlannerOutput != Authority`
- `DO => Receipt`
- `Authority_new => explicit Grant | Delegation | Rule`
- No component may self-certify its own Standing.

## Standing (law; current state lives in STATUS.md)

This section is law, not a status snapshot. The live repo state —
branch, HEAD, what is ALIVE today, PR-progress — is recorded in
`STATUS.md` (repo root); keep it there, never here. See also
`census/2026-jurisdiction-census.md` for the observed (not assumed)
state of the wider ecosystem.

What this repo contains is no longer only the canonical Σ ontology
(`packs/scm-sigma-pack/` + generated JSON Schema projection): since
main @7ac66d8 it also carries the PR-3 machine-enforced jurisdiction
refusal contracts and a prototype vertical slice (`prototype/`:
composition, jurisdiction, verifier, one compound, tests). The
"PR-1 of 5" numbering is historical; STATUS.md tracks what remains.

Standing vocabulary: `ALIVE | PARTIAL_ALIVE | UNKNOWN | BLOCKED |
REFUSED_*`. `ALIVE` requires observed execution, in the claiming
session, against the exact subject. `inspection != execution`;
`importable != alive`; `tests written != tests passing`. Claim no more
than was just executed. The named checks: `scripts/validate_sigma.sh`
(ontology parses, SHACL conforms, generator deterministic, projection
round-trips) and the `prototype/` pytest suite (jurisdiction contracts,
composition). Record command + exit code in STATUS.md. No fabricated
evidence; unknown attribution counts as UNKNOWN, never ALIVE.

## Jurisdiction table (mechanically enforced)

This table is load-bearing, not prose: since PR-3 (merged at main
@7ac66d8), `prototype/tests/test_jurisdiction_contracts.py` parses it
from this file and refuses any drift against
`prototype/jurisdiction.py` — `REFUSED_JURISDICTION_FORBIDDEN` for a
forbidden capability, fail-closed `REFUSED_JURISDICTION_UNKNOWN_COMPONENT`
for a component with no admitted contract. Edit table and registry only
in the same change; the tests reject one-sided edits.

| Repo | Owns | Must not own |
|---|---|---|
| ash_r2rml | Observe (B) | External writes, DO |
| beam4pm | Possibility / Select (Ω, J) | DO |
| ash_a2a | Principal / capability projection (P, Γ) | Canonical human ontology, minting Authority |
| ggen | Construct (μ) | Runtime standing |
| ggen-marketplace | Capability/composition registry (Γ, A, R) | Canonical domain state, execution |
| bcinr | Admission / routing (B, Ω, A) | DO |
| mfw | Narrow authority boundary (A, R) | Freeform planning |
| gymact | Bounded world execution (A, ΔZ, R) | Planning, ontology ownership |
| gitvan | Event identity / temporal provenance (τ, R, B) | Planning, world actuation |
| ggen-ecosystem | Qualification (R, B) | Manufacture semantics, business authority |
| ash_pplan | Composition adapter (P, Ω, τ) | Duplicate lifecycle/queue/planner/runtime |
| autofde-lab | Experiment / qualification env (Ω, J, B, R) | Production authority |
| chatman-ecosystem (this repo) | Meta-A, meta-R, ontology contracts | Product/runtime implementation |
| xaas | Loop coordination / standings write-back (B, J, τ, R) | Canonical human ontology, minting Authority |
| ggen_igniter | Pack manufacture / projection (μ) | DO, Runtime standing |
| zcode-cli | Bounded agent execution (ΔZ, R) | Planning, ontology ownership |
| ash_surface | Surface projection (P, R) | Business authority, DO |
| dfcm-autonomous | Capacity dispatch (A, τ, R) | Product implementation, ontology ownership |

## Remotes and lineage

This checkout is local-only: NO git remote is configured, single
checkout, history lands on `main` via local purpose branches (e.g.
`exp/pr3-jurisdiction-refusal-contracts`, fully merged). There is no
push flow. The GitHub repo `seanchatmangpt/chatman-ecosystem` is an
UNRELATED active lineage sharing only the name — different history, its
own open PRs. Never push to it, open PRs against it, or read its state
as this repo's.

## See also

- `STATUS.md` — current standing, branch/HEAD, verification receipts
  (state lives there; law lives in this file).
- `~/chatman-ecosystem-2030-press-release.md` — the working-backwards
  target state this repo's backwards-chain is closing toward.
