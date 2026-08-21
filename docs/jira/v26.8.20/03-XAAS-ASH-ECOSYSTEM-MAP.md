# v26.8.20 — "XaaS" Coverage Map: This Portfolio's Real Shape, Mapped to the Ash Ecosystem

> Not started, not committed as an implementation ticket. Names the thing the user is calling
> "XaaS" precisely from what's already on disk (rule 1, `criticism-discipline.md`: formalize in
> the user's own system before proposing anything new), then maps the real
> [hex.pm ash-dependent package list](https://hex.pm/packages?search=depends%3Ahexpm%3Aash&sort=total_downloads)
> onto it. Flags one real tension with a prior decision in this same doc set rather than quietly
> overriding it.
>
> **Revision note.** The first pass of this document reviewed only page 1 of the hex.pm search
> (30 packages, sorted by downloads). The user caught the gap. All 5 pages (~127 packages total)
> have now been reviewed; the coverage table below includes the additional real fits that surfaced
> on pages 2–5 — most materially, real **authorization** packages (`ash_policy_authorizer`,
> `ash_rbac`, `ash_grant`, `ash_iam`, `ash_policy_access`), which is a closer match to
> `ce:requiredAuthority`/`ce:brokerRequired` than anything on page 1 covered.

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

### Pages 2–5 (full ~127-package review) — the additional real fits

| Package | Real job | XaaS layer it covers | Concrete fit |
|---|---|---|---|
| `ash_policy_authorizer` | Policy-based authorizer for Ash | SaaS/PaaS (authorization) | Closest real match to `ce:requiredAuthority`/`ce:brokerRequired` on the whole list — every `ce:Capability` individual's authority string becomes a real, enforced Ash policy instead of a TypeScript string checked ad hoc |
| `ash_rbac` | Easier application of RBAC-shaped policies | SaaS (authorization) | Tenant/role-scoped authorization for the owner-only routes (`/api/owner/legal-hold`, `/vendor-offboarding`, `/geofence-policy`) |
| `ash_grant` | Permission-based authorization extension | SaaS (authorization) | Alternative/complement to `ash_policy_authorizer` — evaluate both against the actual `requiredAuthority` string shapes in `ontology/platform-console-capabilities.ttl` before picking one |
| `ash_iam` | AWS IAM-style policy evaluation for Ash | IaaS/SaaS boundary (authorization) | If capability authority strings ever need to compose with real AWS IAM policy documents (the `beamops` Terraform stack already provisions real AWS IAM roles/policies, `modules/cloud/aws/compute/swarm/iam.tf`), this is the direct bridge |
| `ash_commanded` | CQRS via Commanded on Ash resources | SaaS (receipt/replay) | Closer structural match than `ash_events` alone to the `v26.8.19` fact-ownership table's "replay" concept (`docs/jira/v26.8.19/09-CE-REPLAY-1.md`) — commands/events as first-class Ash-modeled objects |
| `ash_event_log` | Automatic event logging/audit trails on resources | SaaS (compliance) | A narrower, more directly-named alternative to `ash_events`/`ash_paper_trail` for `ocel-log.ts` — worth comparing against both before choosing |
| `ash_onetime` | Explicit idempotency / one-time nonce semantics | SaaS/PaaS (receipt discipline) | Direct match for the receipt-idempotency requirement every `ce:Do` capability already carries (`ce:receiptRequired true`) — prevents a capability actuation from being double-applied |
| `ash_circuit_breaker` | Wraps Ash actions in circuit breakers | PaaS (capability actuation) | Fits the fail-closed discipline `ocel-discover-local.test.ts` already exercises ("throws rather than fabricates") — a circuit breaker is the same discipline applied to repeated-failure capability actuation, not just a single call |
| `ash_cookie_consent` | GDPR-compliant cookie consent management | SaaS (compliance) | Direct adjacent fit to `dsar.ts` — consent state is the other half of a real GDPR compliance surface `dsar.ts` alone doesn't cover |
| `ash_oaskit` | OpenAPI 3.0/3.1 spec generator for Ash resources | SaaS/PaaS (API surface) | Generates the OpenAPI spec for whatever `ash_json_api` surface replaces/extends the hand-written `/api/owner/*` routes — real API documentation for free from the same resource definitions |
| `ash_reports` | Comprehensive reporting extension | SaaS (compliance/ops) | Fit for QBR/export/chain-of-custody-shaped capabilities already listed in the platform-console capability set (per `v26.8.19`'s "QBR bundles, export chain-of-custody" commit) |
| `ash_carbonite` | Ash + Carbonite (Postgres audit-trigger/outbox pattern) integration | SaaS (compliance, defense in depth) | A second, DB-trigger-level audit mechanism underneath `ash_paper_trail`/`ash_event_log` — catches writes that bypass the Ash action layer entirely, which an application-level-only audit chain cannot |
| `ash_dispatch` | Event-driven notification system, multiple transport types | PaaS (capability actuation) | Real candidate for the "notify every actor handling tenant X" job `pg` (process groups) was flagged for in `02-ERLANG-RUST-LANGUAGE-SPLIT.md` — an Ash-native alternative if that layer stays in Elixir rather than pure Erlang |
| `ash_agent` / `ash_jido` / `ash_agent_tools` / `ash_agent_session` | LLM/AI-agent integration extensions for Ash | Cross-cutting | A more concrete Ash-native substrate than the single `ash_ai` entry from page 1 if the `autofde-lab` planner's *reasoning* layer (not its actuation boundary, which stays fixed) is ever reimplemented on Ash — still not proposed as an actual migration here |
| `ash_multi_account` | Multi-account linking/switching | SaaS (multi-tenancy) | Direct fit for the tenant-isolation model question `02-ERLANG-RUST-LANGUAGE-SPLIT.md` and the original marketplace-brief both raised (pool vs. silo) — this package assumes a specific shape worth checking against that decision before adoption |
| `ash_kotlin_multiplatform` / `ash_gleam` | Typed client generators (Kotlin Multiplatform / Gleam) from Ash resources | Cross-cutting (frontend bridge) | Same job as `ash_typescript` (page 1), for a different client language — only relevant if a non-TypeScript client ever needs to consume this API surface; no such need identified today |

Reviewed and excluded as no concrete fit (pages 2–5, not exhaustively re-listed): data-layer
packages for stores this system doesn't use (`ash_neo4j`, `ash_scylla`, `ash_age`, `ash_dynamo`,
`ash_cubdb`, `ash_clickhouse`, `ash_sanity`, `ash_arcadic`), ID/type-formatting extensions
(`ash_uuid`, `ash_uuid_v7`, `ash_ulid`, `ash_sqids`, `ash_prefixed_id`, `ash_object_ids`,
`ash_weight`, `ash_slug`, `ash_haikuify`), UI/admin packages that overlap `ash_admin` without a
distinguishing fit (`ash_backpex`, `ash_pyro`/`ash_pyro_components`, `mishka_gervaz`, `ash_panel`,
`green_ash`, `aurora_uix`, `ash_sdui`, `ash_table`, `ash_form_builder`, `runes`, `mob_ash`,
`alva`), translation/i18n (`ash_translation`, `ash_trans`, `ash_phoenix_translations`), and
niche/unrelated integrations (`ash_lua`, `ash_typst`, `ash_thrift`, `ash_meilisearch`,
`search_ash`, `ash_toon_ex`, `ash_baml`, `ash_atproto`, `ash_openfeed`, `steamid`, `diffo`,
`ash_feistel_cipher`, `ash_random_params`, `ash_scenario`, `ash_mock`, `ash_profiler`,
`ash_diagram`, `ash_query_builder`, `ash_default_sort`, `ash_always_select`, `ash_parental`,
`ash_replicant`, `ash_introspection`, `ash_canonical_identity`, `ash_req_opt`,
`ash_phoenix_gen_api`, `ash_postgres_belongs_to_index`, `ash_cascade_archival`, `ash_zoi`,
`ash_sum_type`, `ash_sitemap`, `ash_dyan`, `ash_paper_plane`, `ash_authentication_bankid`,
`ash_authentication_oauth2_server`, `clarity`, `lang_schema`, `mavu_list`, `lavash`,
`reactive_dag`, `foundry_stack`, `tapir`, `elex`, `open_responses`, `pi_ex_native`, `ash_parc`,
`spark_meta`).

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
  — all 5 pages (~127 packages) reviewed as of this revision, not just page 1
- `autofde-lab/CLAUDE.md` — the planner/actuator boundary this doc's layer table is grounded in
- `~/dev/beamops` — the verified-runnable BEAMOps substrate this doc proposes extending
