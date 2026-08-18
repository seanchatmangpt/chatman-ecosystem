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

1. **A real HTTP provisioning API**, not a status stub. `services/ggen/app.py` today answers
   health checks; a PaaS version would expose the equivalent of `ggen sync run` as a POST
   endpoint accepting an ontology and pack list, backed by the same `ggen-engine` functions
   `ggen-cli` and `ggen-mcp` already call — no existing analogue in this repo today.
2. **Pack-registry-as-a-service** behind `services/ggen-marketplace/app.py`, replacing its
   stub with a real network-reachable frontend onto `ggen-marketplace`'s registry types —
   generalizing the `run_pack_query`/`ggen_pack_query` shared-function pattern from one
   SPARQL-search capability to full registry CRUD over HTTP.
3. **A platform-managed signing-key lifecycle** — today `GGEN_SIGNING_KEY` or a local
   `.ggen/keys/signing.key` is a developer's own responsibility; a PaaS tenant should never
   need to generate or rotate this key by hand.
4. **A `rails.toml` entry** (see `catalog/rails.toml`'s 19 named rails, e.g.
   `constitutional_core`, `mcp_boundary`, `gall_checkpoints`) naming this provisioning path
   as an ALIVE or CANDIDATE rail with its own evidence-file pointer, once the HTTP surface
   exists to point at — no existing rail names ggen's sync pipeline as platform behavior
   today.
5. **A frontmatter-declared eligibility contract** for which pack/ontology combinations may
   use unattended dispatch in a PaaS context, extending the existing per-project opt-in to a
   per-tenant one.

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
