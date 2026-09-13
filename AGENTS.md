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

## Status (2026, PR-1 of 5)

This repo currently contains **only** the canonical Σ ontology
(`packs/scm-sigma-pack/`) and one generated JSON Schema projection.
It does NOT yet contain: formal composition-operator laws (PR-2),
machine-enforced jurisdiction refusal contracts (PR-3), an end-to-end
projection-equivalence fixture (PR-4), or a runtime conservation
verifier (PR-5). See `census/2026-jurisdiction-census.md` for the
observed (not assumed) current state of the wider ecosystem.

Do not claim ALIVE for anything beyond: ontology parses, SHACL
conforms, generator is deterministic, and the generated projection
round-trips against the ontology's class set. See
`scripts/validate_sigma.sh` for the exact, currently-passing checks.

## Jurisdiction table (target state — not yet enforced)

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

## See also

- `~/chatman-ecosystem-2030-press-release.md` — the working-backwards
  target state this repo's backwards-chain is closing toward.
