# v26.8.20 — Candidate Language Split: Erlang/OTP (PaaS+SaaS) vs. Rust (IaaS)

> Not started, not committed. Recorded per [`01-ROADMAP-TODAY.md`](01-ROADMAP-TODAY.md) §4's
> convention: a candidate future direction gets a decision before it gets a build. This is that
> decision's write-up, not an implementation ticket.

## The proposal

Split `platform-console`'s implementation language by layer instead of picking one language for
the whole stack, with ggen generating the repetitive scaffolding on both sides from the same
capability ontology (`ontology/platform-console-capabilities.ttl`):

- **Erlang/OTP for PaaS + SaaS** — control plane, tenant isolation, entitlement/plan-state
  machines, capability supervision.
- **Rust for IaaS** — provisioning logic, k8s operators/controllers, compute- or systems-bound
  work.

## Why the split, not one language

| Concern | Erlang/OTP | Rust |
|---|---|---|
| Fault isolation for capability actuation (autofde-lab, gymact, k8s fault-scan) | Supervisor trees make bounded, restartable units a runtime primitive, not a bolt-on | No BEAM-equivalent; would need `tokio` + an actor-supervision crate (e.g. `ractor`) hand-rolled to reach OTP-equivalent guarantees |
| Entitlement / plan-state machine (`app/lib/plan-state.ts`, extended per `v26.8.19`) | `gen_statem`/`gen_server` is exactly this shape | Achievable, no idiomatic runtime-native fit the way OTP has |
| Multi-region/multi-cluster distribution | Near-free via OTP distribution | Hand-rolled |
| Per-tenant isolation (`legal-hold`, `geofence-policy`, `vendor-offboarding`, `retention`) | Actor-per-tenant makes process isolation the actual isolation boundary, not a mental model layered on shared memory | Isolation would be enforced by convention/type discipline, not the runtime |
| Zero-downtime control-plane updates | Hot code loading | None — deploys are restarts |
| Compute-heavy work (crypto, parsing, k8s API churn, solver work) | Weak fit; would need Rust NIFs/ports | Strong fit |
| k8s controllers/operators, Crossplane-style provisioning | Not idiomatic | Strong fit; `praxis-graphlaw` is existing, proven evidence of this lane already working in this ecosystem |
| Compile-time vs. runtime safety guarantee | Runtime, via supervision | Compile-time, via the type system — different mechanism, comparable safety story |

## What makes this viable rather than just theoretically nice

The usual cost objection to Erlang — verbose supervisor/`gen_server` boilerplate written by hand
per capability — is exactly what `ggen`'s six-pack pipeline (schema/crate/routing/behavior/
boundary/verification) already exists to absorb, per [`ggen` skill]. The same TTL-individual
pattern already used to generate the Rust CLI scaffolding would generate OTP supervision trees
and `gen_server` boilerplate from the capability ontology; hand-written logic stays exactly where
`ggen`'s existing convention puts custom behavior (`cnv:CustomBehavior` → a non-overwritten
handler file), on both sides of the split.

## Real state today

Nothing in this split exists yet. `platform-console`'s control plane and compliance surface
(`legal-hold.ts`, `vendor-offboarding-attestation.ts`, `geofence-enforcement.ts`, `plan-state.ts`,
`audit-db.ts`) is TypeScript/Next.js today, not Erlang. The only Rust presence in the ecosystem
cited as precedent is `praxis-graphlaw`, a separate project — no Rust IaaS controller exists
inside `platform-console` itself yet. `ggen`'s six-pack pipeline is proven for Rust CLI generation
in this ecosystem; it has not been exercised against an OTP/Erlang target.

## What a real decision would require before this becomes a ticket

1. A concrete migration boundary: which existing TypeScript control-plane module ports first
   (candidate: `plan-state.ts`, since it's already `gen_statem`-shaped) and what the interop
   surface with the remaining Next.js app looks like during transition (BEAM ports vs. HTTP vs.
   NIFs is itself a real design question, not assumed).
2. Confirmation `ggen` can actually target OTP scaffolding — today this is asserted as plausible
   by analogy to the Rust six-pack, not demonstrated.
3. An explicit call on whether `platform-console` becomes a polyglot deployment (Erlang release +
   Rust binaries + the existing Next.js frontend) and what that does to the current single-app
   Dockerfile/Helm chart (`platform-console/chart/platform-console/`, `app/Dockerfile`).

None of the above has started. This document exists so the tradeoff isn't re-litigated from
scratch if the option is picked up later.

## See Also

- [`01-ROADMAP-TODAY.md`](01-ROADMAP-TODAY.md) — this session's real in-flight work and the
  candidate-future-directions list this document elaborates on
- `ggen` skill — six-pack generation pipeline (schema/crate/routing/behavior/boundary/
  verification) referenced above as the scaffolding-generation mechanism
- `ontology/platform-console-capabilities.ttl` — the capability ontology any generated
  scaffolding on either side of the split would render from
