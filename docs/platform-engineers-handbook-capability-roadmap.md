# The Platform Engineer's Handbook — Capability Roadmap

> **Provenance record.** Companion to
> [`platform-engineers-handbook-ggen-packs.md`](platform-engineers-handbook-ggen-packs.md) and
> [`platform-engineers-handbook-colima-runtime.md`](platform-engineers-handbook-colima-runtime.md).
> This document synthesizes findings already gathered across those two docs plus a same-session
> full-stack composition attempt into one roadmap: what it would take to evolve Ch05's demo app
> into a complete self-serve enterprise platform across full-stack, MLOps, AIOps, DevOps, and
> RevOps. It condenses prior work; it does not re-verify claims already recorded elsewhere, except
> where noted.

## Full-stack

**What exists today.** Ch05's demo app
(`/tmp/platform-engineers-handbook-src/Ch05/demo-app/`) is an intentionally minimal in-memory
CRUD toy — no database, no auth, no frontend, no multi-tenancy — wrapped in solid Kubernetes
plumbing (HPA, PDB, probes, non-root container). Three other chapters each have one real working
slice that was never wired back into it: Ch03 (Keycloak identity), Ch06 (Backstage + OIDC), Ch07
(onboarding API + audit log + RBAC delegation, live-validated end to end on the running colima
cluster per `platform-engineers-handbook-colima-runtime.md`).

**Composition attempt (this session).** A real attempt to close this gap via `ggen` — not a
hand-port of Ch05's Flask app, and not a description of what composition *should* produce — was
run against `nextjs-ai-sdk-pack` from `ggen-marketplace`, real binary, real gates, real receipt
signing. The unmodified attempt's own report, quoted in full below because it is the section's
centerpiece:

> Everything is confirmed real and correctly wired. Here's the full report.
>
> **ggen version:** `26.8.8` (project has this installed). The pack's own maturity note documents
> verification against `26.8.6` — a real 2-patch-version drift, not ignored. No behavioral
> difference was observed in this composition; nothing in the run indicated version-specific
> incompatibility.
>
> **authStrategy = Keycloak/OIDC-compatible: NOT achievable.** This is a real, gate-enforced
> limitation, confirmed by reading the gate before writing any instance data (not discovered by
> trial and error): `gates/030_constraints.rq` line 5 hard-refuses any `nai:authStrategy` value
> outside `("better-auth", "none")`. The ontology and templates only implement Better Auth
> (`lib/auth.ts` imports `better-auth` directly, hardcoded, not templated by strategy value — the
> `authStrategy` fact only gates which literal string is *allowed*, it doesn't branch template
> logic to a different auth library). So Ch03's Keycloak realm-provisioning pattern has no
> composition seam in this pack today. Used `"better-auth"` as the closest real, working,
> gate-admitted value. This is disclosed inline in the instance-data `.ttl` file's header comment
> as well.
>
> **databaseDialect = "postgres": achievable and used**, the real seam for Ch09's Crossplane
> `PostgreSQLClaim` pattern (not wired live in this task, per constraints).
>
> **Dry-run pass 1** (`ggen sync run --dry-run`): 51 files planned, all gates passed cleanly (no
> refusal rows), `graph_hash_hex: d890a52e...`.
>
> **Dry-run pass 2** (identical repeat, before any real write): also 51 planned writes — expected
> and honest to report as such, since dry-run never touches disk, so two dry-run passes against an
> untouched directory necessarily report the same plan both times. This literal two-dry-run
> sequence proves gate-cleanliness twice, not idempotence.
>
> To actually prove the pack's documented "zero pending writes on the second pass" / fixed-point
> claim, the real sequence was run: **`ggen sync run` (real) → `ggen sync run --dry-run` →
> `ggen sync run` (real again) + byte comparison**:
> - Real run 1: wrote 51 files.
> - Dry-run after real run 1: `written: 0`, `skipped: 51`, every skip reason `"unchanged: content
>   identical"` — genuine zero-pending-writes convergence.
> - Real run 2 + SHA-256 byte comparison of all 51 generated files against run 1: **byte-identical**
>   (only `.ggen-v2/receipt.json`, the sync receipt itself, differs — expected, it's not a template
>   output).
> - `ggen receipt verify`: `{"valid": true, "signed": true, "signature_valid": true, "outputs": 51}`.
>
> **Real sync run — files written (51):** package.json, next.config.ts, tsconfig.json,
> components.json, postcss.config.mjs, .env.example, .gitignore, ui-registry.lock.json,
> scripts/verify-ui-registry.mjs, lib/utils.ts, app/globals.css, app/layout.tsx, app/page.tsx,
> lib/ai/{models,tool-broker,tool-handlers,tools,agent,types,tool-contracts}.ts,
> app/api/chat/route.ts, app/api/health/route.ts, lib/auth.ts, lib/auth-client.ts,
> app/api/auth/[...all]/route.ts, proxy.ts, lib/db/{schema,index}.ts, drizzle.config.ts,
> components/chat/chat.tsx, instrumentation.ts, vitest.config.ts, tests/tool-boundary.test.ts,
> playwright.config.ts, tests/e2e/chat.spec.ts, vercel.json, scripts/verify-projection.mjs,
> lib/receipts/{canonical-json,blake3}.ts, components/auth/auth-gate.tsx, scripts/migrate.ts,
> drizzle/0000_nextjs_ai_sdk.sql, scripts/verify-gates.py, ADVERSARIAL_REVIEW.md, README.md,
> components/ui/button.tsx, components/ai-elements/{conversation,message,prompt-input,tool,
> confirmation}.tsx. (Plus `ggen.lock`, `.ggen/keys/{signing,verifying}.key`,
> `.ggen-v2/{receipt.json,receipt-log.jsonl}` as engine-generated artifacts, not pack templates.)
>
> **Spot-checked for real substitution (confirmed, no leaking placeholders):**
> - `package.json`: `"name": "platform-demo-app"` ✓
> - `lib/ai/models.ts`: real model IDs `openai/gpt-5.4` (primary), `anthropic/claude-sonnet-5`
>   (fallback) ✓
> - `lib/ai/agent.ts`: real instructions text, `stopWhen: stepCountIs(8)`, `isEnabled: true`
>   (telemetry) ✓
> - `lib/ai/tools.ts`: `notes_list` tool with real description and `inputSchema`, routed via
>   `broker.invoke("notes.list", ...)` ✓
> - `lib/db/index.ts` / `drizzle.config.ts`: real Postgres/Neon/Drizzle wiring,
>   `dialect: "postgresql"` ✓
> - `lib/auth.ts`: real Better Auth + Drizzle adapter wiring ✓
>
> **Honest scope assessment:** this is narrower than "the full-stack gap closed via composition,"
> and the narrowness is precisely what's stated above — auth is Better Auth, not Keycloak/OIDC (a
> genuine ontology/gate limitation, not something more instance data could fix). What *is* closed:
> a real, gate-verified, deterministically-regenerating, receipt-signed full-stack Next.js 16 +
> AI SDK 7 app (Postgres persistence, Drizzle schema/migrations, an approval-gated read tool wired
> end-to-end from ontology fact → agent → tool → real handler → real DB table, BLAKE3 tool
> receipts, OpenTelemetry instrumentation scaffolding) was manufactured from RDF facts via the
> real `ggen` binary against the real, unmodified `nextjs-ai-sdk-pack`, with two-pass determinism
> and signature verification all confirmed live — not hand-authored, not hand-ported from Ch05's
> Flask app.
>
> **Scratch consumer directory (left in place):** `/tmp/peh-fullstack-consumer/`
> - `ggen.toml` — consumer manifest (`[ontology].source="ontology.ttl"`,
>   `[templates].dir="consumer-templates"` empty placeholder, `[packs]` pointing at the real pack
>   path — avoids the FM-WRITE-008 duplicate-output bug per the tutorial's documented pattern)
> - `ontology.ttl` — the real instance-data facts (Application/Model/Model/Agent/Tool individuals)
> - 51 generated project files under it (package.json, lib/, app/, components/, tests/, etc.)

**Reusable, and from where.** The generated app's Better-Auth-plus-Drizzle-plus-Postgres slice is
now a real reference for wiring Ch09's `PostgreSQLClaim` pattern behind `lib/db/index.ts`; its
BLAKE3 tool-receipt and approval-gated tool-broker pattern is a candidate substrate for the
AIOps guardrail/audit logic below.

**Concrete gap list.**
- Keycloak/OIDC has no composition seam in `nextjs-ai-sdk-pack` today — closing it means adding a
  templated auth-strategy branch to the pack itself, not writing more instance data.
- `databaseDialect = "postgres"` was set but never wired to a live Crossplane `PostgreSQLClaim` —
  the seam exists, the live connection doesn't.
- No multi-tenancy model exists anywhere in the composed output (Better Auth's single-tenant
  default was accepted, not extended).
- The generated app was never deployed to the live `kind-platform-eng-colima` cluster — it exists
  only in `/tmp/peh-fullstack-consumer/`.

## MLOps

**What exists today.** Zero real MLOps infrastructure anywhere in the book or
`ggen-marketplace` — no model registry, training-job scheduler, feature store, experiment
tracking, or data-versioning system.

**Reusable, and from where.** Two shapes, not implementations:
- Ch09's XRD/Claim pattern (`platform-engineers-handbook-ggen-packs.md`'s documented
  `PostgreSQLClaim`/Composition/provider-kubernetes flow, RBAC and schema bugs now fixed and
  shipped in pack `v0.3.0`) is a directly cloneable template for a future
  `ModelDeploymentClaim`.
- Ch14's `AIAgentMetrics`/`PrometheusRule` pattern is a directly cloneable template for
  model-drift monitoring, and it has somewhere real to plug into: the Ch04
  `kube-prometheus-stack` is already live on `kind-platform-eng-colima`
  (`platform-engineers-handbook-colima-runtime.md`, confirmed via a real PromQL query against the
  running Prometheus).

**Concrete gap list.** Model registry, training-job scheduler, feature store, experiment
tracking, data versioning, and the `ModelDeploymentClaim` XRD itself — all net new, none started.

## AIOps

**What exists today.** Ch14's correlation math (`alert-correlator.py`), guardrail/approval/audit
logic (`ai-guardrails.py`), and confidence-threshold framework are real, working, reusable code —
already independently exercised (`test-ai-agents.py`, 15/15 structural checks passing per
`platform-engineers-handbook-ggen-packs.md`).

**Reusable, and from where.** The correlation and guardrail logic itself; and
`docs/75-jidoka-andon-pokayoke.md`'s abnormality-event schema
(`E=(subject,stage,type,evidence,impact,next_safe_actions)`) as a rigorous typed-event model
worth adopting for `alert-correlator.py`'s output — it is design/math prose, not code, so
adopting it means implementing the schema, not importing a library.

**Concrete gap list.**
- The alert source is hardcoded sample data, not live Alertmanager ingestion — despite
  Alertmanager already running live on `kind-platform-eng-colima` as part of the Ch04
  `kube-prometheus-stack`.
- Remediation execution always simulates success; there is no real remediation-action executor.

## DevOps

**What exists today.** Ch07 onboarding is live-validated end to end on the running colima
cluster: real `POST /teams` request, real generated namespace and quota, real RBAC bindings,
verified idempotent on re-POST, real audit-log entries
(`platform-engineers-handbook-colima-runtime.md`). Ch09 Crossplane's three bug fixes (XRD schema
gap, missing RBAC, provider/providerconfig apply-ordering) are proven — each reverified end to
end on separate disposable Kind clusters — and shipped in the `ggen-marketplace`
`platform-engineers-handbook` pack as of `v0.3.0`. Crossplane itself is not installed on the
persistent `kind-platform-eng-colima` cluster, so none of those three fixes have been exercised
there. Ch08's real CI/CD tooling (`pipeline-composer.py`, canary/blue-green deployment,
`rollback-controller.py`) has never been exercised against the live cluster at all, despite its
Istio and Prometheus dependencies already being live there.

**Reusable, and from where.** `github-actions-pack` in `ggen-marketplace` is a confirmed real
generator with SPARQL refusal gates; it could formalize Ch08's golden paths into an actual
generated pipeline rather than the chapter's standalone scripts.

**Concrete gap list.**
- Crossplane not installed on `kind-platform-eng-colima` — the fixes exist and are proven
  elsewhere, but not wired to the live cluster.
- Ch08's CI/CD tooling never run against the live cluster.
- Redis, Kafka, and object-storage self-service claims: no XRD or pack covers any of them.
- Ephemeral preview environments: no XRD or pack covers this either.

## RevOps

**What exists today.** The confirmed-honest total gap. Ch12 is infra cost *attribution*
(OpenCost, internal team/cost-center labels) — not customer billing.
`docs/post-agi-platform-handbook/part-12-economic-closure/{46-finops,47-capability-markets,
48-post-labor-economics}.md` (52, 50, and 58 lines respectively, confirmed by direct read) are
pure philosophy/math prose — no schema, no code, nothing implementable as-is. The marketplace's
`fde20-revops-pack` is enterprise sales-process governance (Challenger methodology), not
billing or metering — a naming false-positive worth flagging explicitly so nobody reaches for it
expecting a billing system.

**Reusable, and from where.** Two fragments, neither a system: Ch12's cost-attribution labeling
convention, and the hash-chained receipt/evidence mechanism (`mfact-pack`) as a *possible*
event-sourcing substrate for a future usage ledger. Nothing today converts a receipt into a
money/usage-unit ledger entry.

**Concrete gap list.** No metering, no pricing engine, no invoicing, no subscription-lifecycle
management, no tenant billing dashboard — anywhere in the book or the marketplace.

## Honest conclusion

RevOps and MLOps are near-total gaps requiring net-new design; nothing in the book or the
marketplace gets either domain past "here is a reusable fragment." DevOps and AIOps are the
opposite shape: both have substantial real, working, independently-tested code
(`ai-guardrails.py`, `alert-correlator.py`, the three shipped Ch09 Crossplane fixes, Ch08's
pipeline tooling) that is simply not wired to the live `kind-platform-eng-colima` cluster —
closing those gaps is an installation and integration problem, not a design or implementation
problem. Full-stack is the one domain with a real composition attempt behind it this session: the
`ggen` run against `nextjs-ai-sdk-pack` genuinely produced a working, receipt-verified,
two-pass-deterministic full-stack app, and it is real progress — but it explicitly could not
compose Keycloak/OIDC (a hard pack-level gate refusal, not a workaround-able limitation) and was
never deployed to the live cluster, so it closes part of the full-stack gap, not all of it.

## If you build one thing next

- **Full-stack** — add a templated auth-strategy branch to `nextjs-ai-sdk-pack` (Keycloak/OIDC
  alongside Better Auth), since the gate that currently refuses it is the only blocker; then wire
  the already-set `databaseDialect = "postgres"` fact to a live `PostgreSQLClaim`.
- **DevOps** — install Crossplane on the live `kind-platform-eng-colima` cluster and apply the
  already-fixed Ch09 pack content (`v0.3.0`); this is now just wiring, not new fixing.
- **AIOps** — replace `alert-correlator.py`'s hardcoded sample feed with real Alertmanager
  webhook ingestion, since the correlation logic itself is already solid and Alertmanager is
  already live on the same cluster.
- **MLOps** — build a `ModelDeploymentClaim` XRD by cloning Ch09's `PostgreSQLClaim` shape; the
  pattern to copy from is proven, only the model-specific schema is new.
- **RevOps** — this is the one requiring genuine net-new architecture, not a quick win. There is
  no billing seam to wire into and no adjacent working code to extend; a metering/pricing/
  invoicing system would have to be designed from the cost-attribution and receipt-chain
  fragments up, not assembled from existing parts.

## See also

- [The Platform Engineer's Handbook — ggen Pack](platform-engineers-handbook-ggen-packs.md)
- [The Platform Engineer's Handbook — Running on Colima](platform-engineers-handbook-colima-runtime.md)
- [75. Jidoka, Andon, and Poka-Yoke for Autonomous Software Manufacture](75-jidoka-andon-pokayoke.md)
