# 02 — ggen as PaaS

Part of [00-OVERVIEW](00-OVERVIEW.md). This ticket proposes what ggen would look like as a
platform-as-a-service tenant of `platform-console` rather than a repo a developer clones and
runs `ggen sync run` in by hand. Today `platform-console/services/ggen/app.py` and
`platform-console/services/ggen-marketplace/app.py` exist only as bare health/status stub
microservices alongside `autofde-lab`, `gymact`, `oidc-idp`, `platform-prober`, and
`vuln-scanner` — ggen is currently a status tenant of the console, not a provisioned service.
A real PaaS ggen would take over everything a developer currently does by hand around the
sync pipeline — pack resolution, SPARQL gate validation, `mode = "Create"`/`"Overwrite"`
semantics, toolchain pinning, receipt signing and verification — as managed platform
behavior, the same way `platform-console` already provisions a per-tenant Postgres/GoTrue/
PostgREST stack from a POSTed CRD instead of asking a developer to run `initdb` themselves.

## What "PaaS" concretely means here

`platform-console/README.md` names its own honesty bar for the term: "This is not a claim of
hyperscaler-grade infrastructure ... it is a single-node local kind cluster." The same
discipline applies here. ggen-as-PaaS does not mean ggen becomes a hosted SaaS with tenants
who never see internals (that is [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md)'s layer) — it means
the sync pipeline becomes a managed, API-driven capability that a developer or another
ecosystem service consumes without owning the toolchain, the signing key lifecycle, or the
`.ggen-v2/receipt.json` file on their own disk. The console already draws this line for
Postgres provisioning: a developer does not SSH into a pod and run `initdb`; they POST a
`Project`/`SingleDatabase` CRD and poll `status.conditions[Ready]`. ggen-as-PaaS is the same
shape, applied to `ggen sync run`.

## The real precedent: one implementation, three access modes

This is not a speculative pattern. It already exists in miniature for one capability. This
session added a `ggen pack query <sparql> [--pack-id <id>]` CLI verb and a matching
`ggen_pack_query` MCP tool (`crates/ggen-mcp/src/tools/pack_query.rs`), and both call one
shared function, `ggen_marketplace::packs_registry::sparql_executor::run_pack_query`. A human
runs the CLI verb; an agent calls the MCP tool; both paths execute the identical SPARQL
query logic against the identical pack registry, with zero duplicated business logic between
them. That is the PaaS pattern already proven at the scale of one capability (pack-registry
search): one implementation function, N access surfaces (human CLI today, agent MCP today,
and by direct extension an HTTP endpoint tomorrow). Generalizing this same pattern from "pack
query" to "full sync-pipeline provisioning" is the core engineering claim of this ticket —
not a new architecture, just the existing one applied to a bigger surface: `ggen-engine`'s
five-stage pipeline (Resolve → Enrich → Extract → Render → Write, `crates/ggen-engine/src/
sync.rs`) instead of one read-only SPARQL executor.

`ggen-mcp` itself is the existing agent-facing control API this PaaS layer would build on,
not reinvent. It is already an MCP server (`rmcp` over stdio) exposing ggen's SPARQL/
frontmatter/diagnostic introspection surface as typed tool calls, read-only except one
`destructiveHint`-annotated tool (`ggen_write_apply`, which refuses to run without an
explicit `confirm: true` argument). A PaaS HTTP API is not a parallel system to `ggen-mcp` —
it is a third transport (HTTP, alongside stdio-MCP and CLI) over the same underlying
functions, matching the `run_pack_query` precedent exactly.

## The provisioning flow, by analogy to the console's real Postgres flow

Illustrative, not existing: a developer (or CI job, or another ecosystem service) would POST
something shaped like `{ontology: <ttl>, packs: [<pack-id>, ...]}` to a ggen provisioning
endpoint, the same way the console today POSTs a `Project`/`SingleDatabase` CRD to provision
Postgres. The platform would resolve the requested packs against `ggen-marketplace`'s
registry (real: `crates/ggen-marketplace/src/marketplace/network.rs` for the HTTP registry
client, `registry_rdf.rs` for the oxigraph-backed RDF registry, `packs/lockfile.rs` for
`packs.lock` integrity digests), run the sync pipeline server-side using a
platform-controlled signing key rather than a developer's local `.ggen/keys/signing.key`
(real: `crates/ggen-engine/src/keys.rs`), and return generated artifacts plus a receipt the
caller can independently verify against `.ggen-v2/receipt.json`'s BLAKE3 chain
(`crates/praxis-core/src/receipt_record.rs`) without ever running `ggen sync run` on their
own machine or managing key rotation themselves.

`ggen-marketplace`'s 147+ packs, which today live in the standalone `~/ggen-marketplace`
content repo and are validated with `python3 scripts/marketplace.py validate`, become this
PaaS's buildpack catalog in the same sense a Heroku-style PaaS ships a fixed set of language
buildpacks — the platform, not the developer, decides which packs are trusted and available,
and pack trust-tier enforcement is already real and already fails closed
(`crates/ggen-marketplace/src/marketplace/install.rs`'s `Installer::verify_trust_tier`
returns `Err`, not a warning, consulting `profile.rs`/`trust.rs`).

## Auto-provisioning without a human decision step: the unattended-dispatch precedent

A PaaS "deploy" button implies some requests get fulfilled without a human or LLM in the
loop reviewing the diff first — but `CONSTITUTION.md`'s "Zero unreceipted actuation"
invariant and BRCE's status as the only lawful DO path do not bend for convenience. ggen
already has a narrow, deliberate answer to exactly this tension: `ggen-mcp`'s Bounded
Unattended-Write Dispatcher (`crates/ggen-mcp/src/tools/unattended_dispatch.rs`,
`try_unattended_apply`). It allows a real write with zero human/LLM decision step, but only
when the target project's own frontmatter template opts in
(`unattended_write_eligible: true`, itself refused unless `unless_exists: true` is also set),
the target file is absent and unprotected, a dry run's entire write-set is covered by the
eligible class, and circuit-breaker budget remains. Every such write is tagged in its own
receipt (`ReceiptRecord::origin = "unattended-dispatch"`, excluded from the chain hash so it
cannot be mistaken for an attended write) and logged to
`.ggen/unattended-dispatch-log.jsonl` on every attempt, success or not — so a human or LLM
reviewing history can always tell which writes bypassed review. This is the exact model a
PaaS auto-provisioning path needs: narrow, opt-in, receipted, logged on every attempt, and
explicitly not the CP21-style "any trigger → any action" general dispatcher that was
assessed and rejected as unsafe in ggen's own governance history. See
[04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) for how this maps onto BRCE more
generally, across all three layers.

## What would need building

1. **DONE (built and tenant-scoped; live-pod status unverified): a real HTTP provisioning
   API.** `platform-console/services/ggen/app.py` (560 lines) is no longer a status stub — it
   implements `POST /provision`, which materializes a real per-tenant-namespaced project
   directory, runs the real `ggen` CLI's `sync run` and `receipt verify` via `subprocess`
   (`run_ggen()`, `app.py:275-285`), and returns the real `.ggen-v2/receipt.json`
   BLAKE3-chained receipt plus its own `receipt verify --format json` output
   (`provision()`/`_provision_inner()`, `app.py:312-481`). This was independently verified this
   session: `receipt_verification.signature_valid: true` on a real run. Beyond this ticket's
   original description, `/provision` now also requires a `project` field and resolves a real
   per-tenant Kubernetes namespace for it (`resolve_tenant_namespace()`, `app.py:214-236`),
   tags every response `"origin": "ggen-paas-provision"`, and appends one JSON line per
   attempt — success or failure — to `PROVISION_LOG_PATH` (`append_provision_log()`,
   `app.py:238-249`). **Not yet fully closed**: `platform-console/k8s/services-and-
   deployments.yaml:489` now points the `ggen-status` Deployment (namespace `ggen`) at
   `image: platform-console/ggen-status:v26.8.18-live` (no longer `:latest`), so the manifest
   has moved past the prior stub image — but this pass could not reach a live cluster
   (`kubectl get pods -n ggen` timed out) to confirm the running pod is actually serving this
   code rather than an older build. The code exists, is tenant-scoped, and is verified locally;
   whether the live pod is running it is unverified, not confirmed-false.
2. **OPEN: pack-registry-as-a-service.** `platform-console/services/ggen-marketplace/app.py`
   is still a 51-line minimal stdlib stub exposing only `GET /healthz` and `GET /status`
   (build-time-baked `facts.json`) — no registry CRUD, no `run_pack_query`/`ggen_pack_query`
   generalization over HTTP. Unchanged from the state this ticket originally described.
3. **DONE: a platform-managed signing-key lifecycle**, landed as part of item 1's same
   `services/ggen/app.py`. `resolve_signing_key()` (`app.py:251-269`) resolves, in order, an
   operator-injected `GGEN_SIGNING_KEY` env var (e.g. from a k8s Secret), a previously-generated
   key at `SIGNING_KEY_PATH`, or a freshly generated 32-byte hex seed persisted with `0600`
   permissions — the caller of `/provision` never supplies or sees a key. This satisfies the
   ticket's original ask ("a PaaS tenant should never need to generate or rotate this key by
   hand") at the single-service level; it does not yet cover per-tenant key isolation across
   multiple ggen-PaaS tenants, since today there is exactly one such service instance.
4. **PARTIALLY DONE: a `rails.toml` entry.** `catalog/rails.toml` now has a rail with
   `id = "ggen"`, `standing = "PARTIAL_ALIVE"`, evidencing exactly `platform-console/services/
   ggen/app.py` and this ticket file — confirmed by reading the file directly. This is a single
   repo-level rail, not the `ggen_iaas`/`ggen_paas`/`ggen_saas` per-layer split
   [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) proposes; that per-layer split
   itself remains open.
5. **OPEN: a frontmatter-declared per-tenant eligibility contract** for unattended dispatch in
   a PaaS context. `unattended_write_eligible` remains scoped to per-project frontmatter in
   `ggen-engine`/`ggen-mcp` (`crates/ggen-mcp/src/tools/unattended_dispatch.rs`,
   `crates/ggen-engine/src/template.rs`); no per-tenant extension exists. Unrelated to this
   ticket's scope but confirmed real and unrelated: `platform-console/app/lib/redis.ts` and
   `platform-console/app/lib/queue.ts` (a `nats:2-alpine`-backed queue, not a ggen construct)
   landed this session as real per-project managed addons — they provision Redis/NATS
   Deployments for arbitrary console projects and do not touch ggen's sync pipeline, signing
   keys, or unattended-dispatch eligibility, so they close none of this item's gap.

## See Also

- [00-OVERVIEW](00-OVERVIEW.md) — index for this ticket set
- [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — the infrastructure layer this PaaS layer is built on
- [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — the tenant-facing layer built on top of this PaaS
- [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) — how BRCE's zero-unreceipted-
  actuation invariant binds all three layers, including this ticket's unattended-dispatch
  precedent
- `/Users/sac/chatman-ecosystem/docs/40-ggen-semantic-manufacturing-system.md` — the formal
  `ggen:(O*,Q,G_r,V_a,P)->(T,R_d)` signature this ticket's provisioning flow implements as a
  network-reachable capability
- `/Users/sac/chatman-ecosystem/SONY-READINESS-GAP-CLOSURE.md` — the existing IaaS/PaaS/SaaS
  layering applied to `platform-console` generally, whose PaaS-layer gaps (e.g. "vulnerability
  scan as a hard admission gate") this ticket's proposal would also need to satisfy once a
  real ggen provisioning endpoint exists
