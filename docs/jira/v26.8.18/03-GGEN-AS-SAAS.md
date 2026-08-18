# ggen as SaaS

Part of [00-OVERVIEW](00-OVERVIEW.md), the third of three layered design proposals for
ggen inside chatman-ecosystem, above [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) (the compute/
cluster substrate) and [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) (self-service provisioning
for developers who still author ontologies). This ticket is the layer where
`docs/41-ggen-marketplace-civilization-memory.md`'s "civilization memory" framing for
ggen-marketplace stops being a metaphor and becomes the literal product surface: an end
user never sees SPARQL, TTL, or `ggen.toml`. They browse a catalog and buy a capability —
"give me a compliant Next.js CRUD app," "give me an ERRC-analyzed GitHub Actions
surface" — and get an artifact plus a receipt, not a repo to configure. No existing
analogue in this repo implements that catalog or delivery path today; this proposes it.

## Why this is not a new concept, only a new audience

ggen's own pack ecosystem in `~/ggen-marketplace` already models "capability" as a
first-class, purchasable/measurable unit — this is a genuine architectural fact, not an
analogy invented for this ticket. Three real packs make the point directly:

- `fortune5-required-capabilities-pack` (26.7.30) — "the bounded 19-capability,
  57-surface Fortune-5 control plane," per its own `pack.toml` description
  (transcribed verbatim in `/Users/sac/ggen/.claude/rules/architecture.md`'s Pack
  Inventory table).
- `pcq-marketplace-pack` (26.8.2) — "a real-time Next.js 16 + deck.gl capability
  marketplace with fixed-supply PCQ settlement, SSE streams, receipts."
- `sbb-capability-density-pack` (26.8.3) — "a density unit is one [Solution Building
  Block]," an explicit admitted quantitative unit for a capability.

A ggen-SaaS product catalog is therefore an act of exposure, not invention: take the
`capability`-as-unit vocabulary that already lives in these packs' ontologies and put a
storefront in front of it. `docs/41-ggen-marketplace-civilization-memory.md` already
frames ggen-marketplace as "civilization memory" — accumulated, reusable, qualified
capability. SaaS is the layer where a non-technical buyer draws on that memory without
knowing it's RDF underneath.

## The receipt chain as the product, not the plumbing

Every other layer in this proposal set treats the BLAKE3 receipt chain
(`crates/praxis-core/src/receipt_record.rs`'s `ReceiptRecord`, chained
`chain_hash_hex`/`prev_chain_hash_hex`/`signature_hex`, written to
`.ggen-v2/receipt.json` + `receipt-log.jsonl`, signed via
`crates/ggen-engine/src/keys.rs`) as developer-facing debugging and reproducibility
infrastructure. At the SaaS layer it inverts: the receipt chain is the thing being sold.
Generic code-generation SaaS products (scaffolding tools, low-code builders) have no
equivalent artifact — they hand back files with no cryptographically verifiable claim
about what produced them, from which inputs, or whether the output has been tampered
with since delivery. ggen already has "proof-of-generation" as a structural property of
every sync. A ggen-SaaS product's differentiator is packaging that proof as the audit
trail a buyer pays for — "here is the receipted chain from your subscribed ontology
state to this exact artifact" — not hiding it behind a download button the way a
conventional SaaS would.

## What Sony-readiness already told us applies unmodified here

`SONY-READINESS-GAP-CLOSURE.md` already ran an IaaS/PaaS/SaaS layering pass against
platform-console as a whole, against an explicit "Sony-level media company" bar. Its SaaS
bucket was written for platform-console generally, but every item in it applies to a
ggen-SaaS product without modification, because a ggen-SaaS product is a platform-console
tenant offering, not a separate system:

- "Tamper-evident, isolated audit log store" — a ggen-SaaS tenant's receipt log
  (`receipt-log.jsonl` per invocation) needs the same tamper-evidence guarantee applied
  to it that the gap-closure doc asked for generally; today nothing in
  `platform-console/services/ggen/app.py` (currently a bare health/status stub, per the
  grounding facts) stores or isolates receipt history per tenant.
- "Content/IP protection primitives (signed, expiring asset URLs)" — a buyer's generated
  Next.js CRUD app or ERRC report is IP the moment it's delivered; ggen-SaaS needs the
  same signed/expiring URL mechanism the gap-closure doc calls for, applied to generated
  artifact delivery rather than left as a bare filesystem path.
- "No multi-tenant billing/metering enforcement tied to hard resource caps beyond
  ResourceQuota" — `k8s/resource-quotas.yaml` (real, cited in the IaaS-layer facts)
  caps compute per namespace but has no concept of "capability invocations purchased" —
  metering has to be a new, receipt-tied concern, not inferred from ResourceQuota.

Because `catalog/rails.toml` already names `evidence` and `receipts` as standing ALIVE
rails with their own evidence-file pointers, the correct fix for all three gaps is to
extend those two rails to cover per-invocation metering and tamper-evidence, not to stand
up a parallel billing/audit system outside the constitution's rail structure. This keeps
the fix inside the same "control plane, not a source-code monorepo" posture
`CONSTITUTION.md` states for the whole repo.

## What would need to be built

1. **Capability catalog UI** — reuses the console app's existing self-service UX pattern
   (the real Next.js console in `platform-console/` that already POSTs
   Supabase-operator-style CRDs and polls `status.conditions[Ready]`, per the PaaS-layer
   grounding facts) but renders pack-registry SPARQL results as catalog cards instead of
   infrastructure forms. `ggen pack query` (this session's real, verified addition —
   `crates/ggen-mcp/src/tools/pack_query.rs`'s `ggen_pack_query` MCP tool plus the
   matching CLI verb, both routed through the one shared
   `ggen_marketplace::packs_registry::sparql_executor::run_pack_query`) is direct
   precedent that pack-registry facts can already be queried by a non-CLI consumer — the
   catalog UI would be that same query surface with a storefront skin, not a new
   query path.
2. **Per-invocation metering tied to receipts** — every `ReceiptRecord` already carries
   a chain hash and (per the ggen workspace's own "Bounded Unattended-Write Dispatcher"
   convention) an `origin` field distinguishing how a write was triggered. Extending
   that pattern with a tenant/subscription identifier and wiring metered usage off real
   receipt emission (not off a separate, driftable counter) satisfies the "reduce
   drift" half of ggen's own coding-agent-mistakes gate: the receipt becomes the sole
   source of truth for what was billed, exactly as it is already the sole source of
   truth for what was generated.
3. **Tamper-evident, isolated audit log store** — the receipt-log rail already exists per
   invocation locally (`.ggen-v2/receipt-log.jsonl`); a ggen-SaaS tenant needs that log
   promoted to isolated, append-only, tenant-scoped storage the tenant (and only the
   tenant) can query — the SONY gap item applied literally, not reinvented.
4. **Signed, expiring asset URLs for delivered artifacts** — illustrative example, not
   existing: when a subscriber's "compliant Next.js CRUD app" capability run completes,
   the delivered archive would be served from a signed URL with an expiry, the same
   primitive SONY-READINESS names for platform-console generally, rather than a bare
   static-file link with no revocation or access boundary.
5. **Trust-tier-aware capability pricing/gating** — `ggen-marketplace`'s existing
   `marketplace/install.rs`'s `verify_trust_tier` (returns `Err`, not a warning — a real,
   already-enforced fail-closed control) is the natural admission gate for which
   catalog capabilities a given subscription tier may invoke; a SaaS pricing tier maps
   onto pack trust tiers that already exist, rather than requiring a new authorization
   model bolted on separately.

## What this ticket does not resolve

Who actually stands up `platform-console/services/ggen/app.py` beyond its current
health-stub state, and how BRCE's "zero unreceipted actuation" invariant constrains a
paid capability invocation from an untrusted external buyer request (as opposed to an
internal PaaS self-service tenant), are cross-cutting authority questions —
[04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) is where that boundary gets
worked out, not here.

## See Also

- [00-OVERVIEW](00-OVERVIEW.md) — index for this ticket set
- [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — the compute/cluster layer this SaaS product
  would run on
- [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — the self-service developer layer this SaaS
  product sits above (buyers never touch the PaaS layer's ontology-authoring surface)
- [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) — BRCE actuation boundary
  questions this ticket defers
- `docs/41-ggen-marketplace-civilization-memory.md` — the "civilization memory" framing
  this ticket makes literal
- `SONY-READINESS-GAP-CLOSURE.md` — source of the three SaaS-layer gaps cited above
