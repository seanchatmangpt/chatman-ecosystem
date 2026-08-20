# v26.8.20 — Candidate Language Split: Pure Erlang/OTP (PaaS+SaaS) vs. Rust (IaaS)

> Not started, not committed. Recorded per [`01-ROADMAP-TODAY.md`](01-ROADMAP-TODAY.md) §4's
> convention: a candidate future direction gets a decision before it gets a build. This is that
> decision's write-up, not an implementation ticket.
>
> **Pure Erlang, not Elixir.** The reference material reviewed for this update —
> *Engineering Elixir Applications* (Fairholm & Giralt D'Lacoste, Pragmatic Bookshelf, 2024,
> `~/Downloads/engineering-elixir-applications_P1.0.pdf`) — is an Elixir/Phoenix book, but its
> "BEAMOps" content (Terraform, Docker/Docker Swarm, GitHub Actions CI/CD, Packer AMIs,
> Distributed Erlang clustering, autoscaling, Grafana/PromEx/Loki instrumentation — chapters 2–12)
> operates at the BEAM/OS/ops layer, not the Elixir-syntax layer, and carries over to a pure-Erlang
> release directly: OTP releases, `epmd`/distribution, and Docker Swarm node discovery don't care
> whether the code above them is Erlang or Elixir. Only the app-layer chapter (Phoenix LiveView,
> ch. 3) is Elixir-specific and has no pure-Erlang equivalent worth adopting wholesale — a pure
> Erlang control plane would expose HTTP via Cowboy directly, or stay headless behind the existing
> Next.js frontend, not port LiveView.

## The proposal

Split `platform-console`'s implementation language by layer instead of picking one language for
the whole stack, with ggen generating the repetitive scaffolding on both sides from the same
capability ontology (`ontology/platform-console-capabilities.ttl`):

- **Erlang/OTP for PaaS + SaaS** — control plane, tenant isolation, entitlement/plan-state
  machines, capability supervision.
- **Rust for IaaS** — provisioning logic, k8s operators/controllers, compute- or systems-bound
  work.

## Most recent OTP features/frameworks first (target: OTP 27/28, not legacy OTP)

A pure-Erlang PaaS/SaaS control plane built today should target current OTP, not the
`gen_server`-only baseline most Erlang material assumes. In relevance order for this platform:

| OTP feature | Version | Why it matters here |
|---|---|---|
| `json` stdlib module | 27.0 | Native JSON encode/decode with no third-party dep — every capability API route (`/api/owner/*`, `/api/ocel/*`) becomes a straight `json:encode/1`/`decode/1` boundary, no `jsx`/`jiffy` NIF dependency to vet |
| `maybe ... end` expressions (EEP 49) | 27.0 (default-enabled) | Chains of fallible steps — legal-hold apply → geofence check → audit-log write — read as flat `maybe` blocks instead of nested `case`, matching the fail-closed error handling this codebase already favors (`ocel-discover-local.test.ts`'s "throws rather than fabricates" test is exactly the discipline `maybe` makes readable in Erlang) |
| `proc_lib:set_label/1` (process labels) | 27.0 | Per-tenant/per-capability actor processes get a real debuggable name in `observer`/crash reports without registering a global atom name — directly solves actor-per-tenant observability at scale |
| Priority messages (EEP 76) | 28.0 | A supervisor or health-check message can jump a capability process's mailbox ahead of queued tenant work — relevant for the same kind of "urgent control signal vs. bulk tenant traffic" split a k8s liveness probe already assumes |
| `tprof` profiling tool | 27.0 | Replaces `eprof`/`fprof`/`cprof` with one tool — relevant for the compute-adjacent capability actuation paths (k8s fault-scan diagnosis) that stay in Erlang rather than shelling to Rust |
| Multiple concurrent trace sessions | 27.0 | Lets an operator trace one tenant's capability actor without the trace conflicting with existing observability tooling (PromEx/Grafana pattern from the BEAMOps book, ch. 11–12) already mid-deploy |
| Native code coverage | 27.0 | CI coverage runs faster without the `cover` compile-to-bytecode overhead — relevant if the ggen-generated OTP scaffolding's own generated tests run in CI per capability |
| Zip/strict generators in comprehensions (EEP 73) | 28.0 | Two aligned lists (e.g., tenant IDs + their geofence policies) iterate as one `[... || X <- Ids && P <- Policies]` instead of `lists:zip` + a fold — minor but real for the compliance-data-shape code this session is writing |

Framework layer, on top of stdlib/OTP:

- **`gen_statem`** (present since OTP 19, still the right primitive) for the entitlement/plan-state
  machine — no version gate, already stable, matches `01-ROADMAP-TODAY.md` §3's note that
  `plan-state.ts` is already `gen_statem`-shaped.
- **`pg`** (process groups, replaced the old `pg2` as of OTP 23) for per-tenant or per-capability
  broadcast groups — the natural Erlang-native primitive for "notify every actor handling tenant
  X," which the SaaS compliance surface (legal-hold, vendor-offboarding) would otherwise reinvent.
  The BEAMOps book's ch. 9 Distributed Erlang chapter uses `pg`/Phoenix PubSub to pass data across
  cluster nodes — the pure-Erlang equivalent is `pg` directly, no PubSub wrapper needed.
- **Distributed Erlang clustering itself** (BEAMOps book ch. 9): join cluster nodes over a private
  network, verified live with a Docker Swarm overlay network in the book's worked example —
  directly reusable for a pure-Erlang multi-node control plane without modification, since
  clustering is a BEAM-level, not Elixir-level, capability.
- **`ggen`-generated OTP scaffolding** (per this doc's original proposal below): supervision trees
  and `gen_server`/`gen_statem` boilerplate rendered from `platform-console-capabilities.ttl`,
  hand-written logic in `cnv:CustomBehavior` handler modules — unaffected by the Erlang-vs-Elixir
  choice, since ggen targets OTP behaviours, which are language-syntax-agnostic (Elixir's
  `GenServer` and Erlang's `gen_server` are the same OTP behaviour with different syntax on top).

Sources: [Erlang/OTP 27 Highlights](https://www.erlang.org/blog/highlights-otp-27/),
[Erlang/OTP 28 Highlights](https://www.erlang.org/blog/highlights-otp-28/).

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
in this ecosystem; it has not been exercised against an OTP/Erlang target. No Erlang or Elixir
runtime exists anywhere in `platform-console` yet — the BEAMOps book above is reference material
reviewed for this update, not a dependency already adopted.

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
- [Erlang/OTP 27 Highlights](https://www.erlang.org/blog/highlights-otp-27/),
  [Erlang/OTP 28 Highlights](https://www.erlang.org/blog/highlights-otp-28/) — the current-OTP
  feature sources cited above
- *Engineering Elixir Applications* (Fairholm & Giralt D'Lacoste, 2024) — BEAMOps ops-layer
  reference reviewed for the Distributed Erlang / Docker Swarm / autoscaling / PromEx-Grafana
  material cited above; app-layer (Phoenix LiveView) content does not carry over to pure Erlang
