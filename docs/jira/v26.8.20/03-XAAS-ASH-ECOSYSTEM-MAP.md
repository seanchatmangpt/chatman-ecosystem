# v26.8.20 — "XaaS" Coverage Map: This Portfolio's Real Shape, Mapped to the Ash Ecosystem

> Not started, not committed as an implementation ticket. Names the thing the user is calling
> "XaaS" precisely from what's already on disk (rule 1, `criticism-discipline.md`: formalize in
> the user's own system before proposing anything new), then maps the real
> [hex.pm ash-dependent package list](https://hex.pm/packages?search=depends%3Ahexpm%3Aash&sort=total_downloads)
> onto it. Flags one real tension with a prior decision in this same doc set rather than quietly
> overriding it.

## What "XaaS" already is, checked against the repos, not invented

Three real, distinct layers already exist across this ecosystem, each with a different job:

| Layer | Repo | Real job | Evidence |
|---|---|---|---|
| Capability ontology (the "what can be done" registry) | `chatman-ecosystem/ontology/{capabilities,platform-console-capabilities}.ttl` | 45 `ce:Capability` individuals in the platform-console slice alone (44 of them `ce:capabilityClass ce:Do`), each carrying `executionOwner`, `requiredAuthority`, `brokerRequired`, `receiptRequired`, `reversible`, `standing`, and an `ce:interface` list (CLI/API/MCP/A2A) | `grep -c "ce:Capability"` = 45; every individual checked carries the full property set |
| Planner / decision control plane (the "what plan is admissible" layer) | `autofde-lab` (submodule, `platform-console/services/autofde-lab`) | "Computes candidate plans. Does not actuate." Explicit boundary: planner selects, broker authorizes, executor performs, verifier evaluates — actuation runs through `gymact`/OpenClaw, never through this repo directly | `autofde-lab/CLAUDE.md`, `.claude/rules/gym-actuation-boundary.md` |
| Compliance/entitlement/API surface (the "what a tenant sees and is bound by" layer) | `platform-console` (this repo, TypeScript/Next.js) | `audit-db.ts`/`ocel-log.ts` (hash-chained audit + OCEL event log), `legal-hold.ts`, `vendor-offboarding-attestation.ts`, `geofence-enforcement.ts`, `retention.ts`, `dsar.ts`, `plan-state.ts` (entitlement state machine), `stripe-billing.ts` | This session's commits `a4742f7`/`2ae76aa`; `v26.8.19/00-OVERVIEW.md`'s fact-ownership-layers table |

"XaaS" is the honest name for these three layers taken together, governed by one discipline:
every `ce:Do` capability requires a broker and a receipt, reversible or not. This is not a new
thing to build — it is the name for what `platform-console` + `autofde-lab` + `gymact` already
are, together. The open question this doc answers is which *implementation substrate* covers the
most of this ground with the least hand-written code, per the user's stated goal.

## The real tension this doc must state, not silently resolve

[`02-ERLANG-RUST-LANGUAGE-SPLIT.md`](02-ERLANG-RUST-LANGUAGE-SPLIT.md) proposed **pure Erlang**
for the PaaS+SaaS control plane specifically because Elixir was ruled out per the prior session's
instruction. The Ash framework and every package in the hex.pm list below (`ash_postgres`,
`ash_state_machine`, `ash_paper_trail`, ...) **is Elixir-only** — Ash's resource DSL is a macro
system with no Erlang equivalent, and no `ash`-for-Erlang exists. Adopting Ash to "cover as much
ground as possible" for XaaS is a real reversal of that prior premise for the SaaS/entitlement
resource layer, not a refinement of it. Rule 4 (`criticism-discipline.md`): stating this plainly,
not carrying the pure-Erlang conclusion forward on momentum. The two are compatible only if scoped
per-concern: Ash/Elixir for resource modeling + API surface (where its coverage is real and large,
per the table below), pure Erlang/OTP kept for the actuation/supervision primitives where BEAM
distribution and supervision — not a resource DSL — are the actual value (capability-actuation
processes, per-tenant isolation actors). That is a genuine split proposal, not a hedge, and it
should be confirmed as the intended reading before code is written either way.

## `~/dev/beamops` as the substrate

Verified this session, real: `mix compile` clean, `mix ecto.migrate` clean, `mix phx.server` →
`GET / → 200` on OTP 28 / Elixir 1.19.5, real Postgres. All 12 BEAMOps book chapters have
corresponding real artifacts (Terraform, Packer AMI, Docker Swarm + autoscaling, PromEx/Grafana/
Loki, `DNSCluster`-based Distributed Erlang). This is the only verified-runnable BEAM project on
disk and the natural host to extend, rather than starting a new Ash app from zero — it already has
Ecto/Postgres, a release pipeline, CI, and production Terraform, which is most of what an Ash app
needs underneath it (`ash_postgres` sits on the same Ecto/Postgres this app already runs).
`~/dev/beamops` is not currently a git repository — `git init` is a prerequisite before real
extension work, not a detail to skip.

Separately: `~/dev` and `~/cns` hold 100+ other `mix.exs` projects, heavily Ash-centered
(`ash_cms`, `ash_yaml`, `ashrddd`, `ash_reactor_zero/secure/pure/80_20`, `ash_swarm`, `gen_ash`,
`infinite_agentic_ash`) — real evidence of prior Elixir/Ash effort, per the user's own account of
struggling with weaker prior models on this stack. None of these were opened or assessed for
salvageability this pass; that is real follow-on work if any of them turn out to hold usable
domain logic rather than scaffolding.

## Ash package → XaaS layer coverage map

Ordered by the real hex.pm `total_downloads` ranking fetched this session, restricted to packages
with a concrete fit against the three layers above:

| Package | Real job | XaaS layer it covers | Concrete fit |
|---|---|---|---|
| `ash_postgres` | Postgres data layer for Ash resources | SaaS (persistence) | Replaces/extends the bare `Kanban.Repo` Ecto usage already in `beamops`; every `ce:Capability` individual becomes an `Ash.Resource` row |
| `ash_state_machine` | State machines as Ash resources | SaaS (entitlement) | Direct match for `plan-state.ts`'s `gen_statem`-shaped entitlement/plan machine, already flagged in `01-ROADMAP-TODAY.md` §2 as the strongest `gen_statem` candidate |
| `ash_paper_trail` | Audit log of changes to Ash resources | SaaS (compliance) | Direct match for `audit-db.ts`'s hash-chained audit log — an Ash-native version instead of hand-rolled TypeScript audit-chain code |
| `ash_events` | Centralized event log tracking resource changes | SaaS (compliance) | Direct match for `ocel-log.ts`'s OCEL event log — same "every capability actuation is a logged event" shape, Ash-native |
| `ash_archival` | Soft-deletion extension | SaaS (compliance) | Direct match for `retention.ts`/`legal-hold.ts` — a legal hold is exactly "refuse archival/deletion for this resource until a condition clears" |
| `ash_authentication` (+`_phoenix`) | Authentication extension | SaaS (identity) | Tenant/owner auth for whatever Ash-native console sits next to or replaces parts of `platform-console`'s Next.js auth surface |
| `ash_json_api` / `ash_graphql` | API extensions | SaaS/PaaS (API surface) | Generates the `/api/owner/*`-shaped REST surface (or GraphQL) directly from `Ash.Resource` definitions instead of hand-written Next.js route handlers per capability |
| `ash_admin` | Super-admin UI (Phoenix LiveView) | SaaS/PaaS (owner console) | Real candidate to cover the "owner" surface (`/api/owner/geofence-policy`, `/legal-hold`, `/vendor-offboarding`) with a generated admin UI instead of hand-built pages |
| `ash_oban` | Ash + Oban background-job integration | PaaS (capability actuation) | The `ce:Do`/broker/receipt actuation loop is background-job-shaped; `ash_oban` is the closest existing primitive to "queue this capability actuation, record its receipt on completion" |
| `ash_double_entry` | Double-entry bookkeeping on Ash resources | SaaS (billing) | Real fit for the entitlement/billing ledger `plan-state.ts`/`stripe-billing.ts` currently hand-roll in TypeScript |
| `ash_cloak` | Field-level encryption for Ash resources | SaaS (compliance) | Fit for whatever PII/compliance fields `dsar.ts`/`vendor-offboarding-attestation.ts` handle that need encryption at rest, not just access control |
| `ash_rate_limiter` | Rate limiting on Ash actions | IaaS-adjacent | Same job as the existing Istio API-gateway rate limiting (`app/api-gateway`), at the application layer instead of the mesh layer — a complement, not a replacement |
| `opentelemetry_ash` | OpenTelemetry integration | Cross-cutting (observability) | Extends the PromEx/Grafana/Loki instrumentation `beamops` already has (book ch. 11–12) with tracing |
| `ash_ai` | Integrated LLM features for Ash apps | Cross-cutting | Candidate substrate for the capability-reasoning layer `autofde-lab`'s planner already occupies conceptually, if the planner itself were ever reimplemented in Elixir (not proposed here — `autofde-lab` stays Python per its own explicit boundary) |
| `ash_typescript` | Generates TypeScript clients from Ash resources | Cross-cutting (frontend bridge) | If `platform-console`'s Next.js frontend stays and an Ash backend sits behind it, this is the real bridge — typed clients generated from the same resources, instead of hand-written `fetch` calls per new API route |

Deliberately excluded from the table (real, but no concrete fit found against this system):
`honeybadger`, `cinder`, `ash_appsignal`, `ash_geo`, `ash_jason`, `aepf_opensearch`,
`smokestack`, `ash_sqlite`, `ash_flow` (soft-deprecated per hex.pm's own listing), `ash_csv`,
`ash_money` (no currency-conversion/multi-currency need identified in the current billing code).

## What this doc does not do

It does not start writing Ash resources. It states the real shape, the real coverage map, and the
one real premise conflict with `02-ERLANG-RUST-LANGUAGE-SPLIT.md` that needs an explicit decision
(full Ash/Elixir for SaaS+PaaS resource/API/admin layers, pure Erlang/OTP kept narrowly for
actuation/supervision) before code gets written under either name.

## See Also

- [`01-ROADMAP-TODAY.md`](01-ROADMAP-TODAY.md) — real in-flight `platform-console` work this
  session, including the `plan-state.ts`/`audit-db.ts`/`ocel-log.ts` code this doc maps onto Ash
- [`02-ERLANG-RUST-LANGUAGE-SPLIT.md`](02-ERLANG-RUST-LANGUAGE-SPLIT.md) — the pure-Erlang
  proposal this doc's tension section is checked against
- [Ash-dependent packages, hex.pm, sorted by total downloads](https://hex.pm/packages?search=depends%3Ahexpm%3Aash&sort=total_downloads)
- `autofde-lab/CLAUDE.md` — the planner/actuator boundary this doc's layer table is grounded in
- `~/dev/beamops` — the verified-runnable BEAMOps substrate this doc proposes extending
