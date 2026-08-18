# ggen as IaaS: the Manufacturing Capsule Layer

This is the bottom layer of a three-layer proposal (IaaS / PaaS / SaaS, mirroring the taxonomy
`SONY-READINESS-GAP-CLOSURE.md` already applies to `platform-console` as a whole) for what it
would concretely take for ggen to register as a rail in `catalog/rails.toml` and become a
first-class provisioned tenant of `platform-console`, rather than the bare status stub it is
today (`platform-console/services/ggen/app.py`). At this layer there are no packs, no ontology
semantics, and no user-facing product surface — only the raw substrate a tenant needs to run
`ggen sync run` lawfully and keep a receipt chain. This layer has no existing analogue anywhere
in chatman-ecosystem today: it is greenfield, unlike the PaaS layer (see
[02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md)), which already has a stub service to build on.

## What "infrastructure" means for a deterministic manufacturing system

Conventional IaaS provisions raw compute: a VM, a block volume, a network interface. ggen is not
a general-purpose compute workload — per `docs/40-ggen-semantic-manufacturing-system.md`, "ggen
should be understood as a deterministic semantic manufacturing system whose outputs include
software but are not limited to software," with the formal signature
`ggen:(O*,Q,G_r,V_a,P)->(T,R_d)`. The thing a tenant actually needs at the infrastructure layer is
not CPU-seconds in the abstract; it is:

1. **Manufacturing capacity** — one isolated instance of the sync pipeline
   (Resolve → Enrich → Extract → Render → Write, `crates/ggen-engine/src/sync.rs` in the ggen
   repo) able to run `ggen sync run` against a tenant-supplied `.specify/*.ttl` and `ggen.toml`,
   backed by a pinned `ggen` binary and its default graph engine (`praxis-graphlaw`, or Oxigraph
   for callers that go through `ggen-graph` directly).
2. **Receipt custody** — durable, tenant-owned storage for the artifact of every sync: the BLAKE3
   receipt chain (`praxis-core::ReceiptRecord`'s `chain_hash_hex`/`prev_chain_hash_hex`/
   `signature_hex`, written to `.ggen-v2/receipt.json` plus the full log at
   `.ggen-v2/receipt-log.jsonl`) and the signing/verifying keypair that authenticates it
   (`crates/ggen-engine/src/keys.rs`: `GGEN_SIGNING_KEY` env var, else `.ggen/keys/signing.key`,
   generated on first real sync if absent, with `.ggen/keys/verifying.key` its public half).

"Disk" at this layer is not a generic PVC — it is specifically the receipt volume plus the key
material, because those two things together are what make a tenant's manufacturing output
admissible evidence rather than an unverifiable file drop. Everything else (the ontology content,
the packs, the rendered output tree) is a PaaS/SaaS concern layered on top.

## Why BRCE's invariant bites hardest here

`CONSTITUTION.md`'s governing equation is `A = mu(O*), R = receipt(A)`: admitted observation to
lawful manufacture to artifact to receipt, under the repeated invariant "Zero unreceipted
actuation" — BRCE is the only lawful DO path; everything else can only submit intentions. At the
PaaS and SaaS layers a tenant interacts through a curated surface (a pack registry, a console, an
API) that can mediate every write. At the IaaS layer, by construction, a tenant has raw access to
ggen's own Write stage — the fifth stage of the sync pipeline that actually touches the
filesystem. That is precisely the point where "zero unreceipted actuation" is easiest to violate
by omission: a tenant capsule that lets `sync run` execute without a receipt volume mounted, or
without signing keys provisioned, produces real filesystem mutation with no admissible evidence
trail — the exact failure mode `CONSTITUTION.md` names ("Derivation receipt != Actuation
receipt") and the exact failure mode ggen's own `docs/jira/v26.7.16/` receipt-chain work exists to
prevent inside the ggen repo. An IaaS layer that provisions compute without provisioning receipt
custody as a co-equal, non-optional resource would reintroduce that gap at the ecosystem boundary
even though ggen itself already closes it internally.

Concretely, this means the IaaS provisioning contract cannot treat the receipt volume as optional
storage a tenant might attach later — the capsule's own admission gate should refuse to start
`sync run` at all if no receipt volume and no keypair are bound, mirroring
`crates/ggen-engine/src/keys.rs`'s own behavior (generate-on-first-sync) but applied at the
capsule boundary instead of inside a single binary invocation.

## What would need to be built (concrete, greenfield)

None of the following exists today. Each item names the real chatman-ecosystem or ggen artifact
it would extend or reuse, per the grounding facts for this ticket set:

- **A capsule provisioning API.** A new endpoint (illustrative example, not existing:
  `POST /iaas/ggen/capsules`) that stands up one isolated `ggen sync`-pipeline instance per
  tenant — pinned binary version, sandboxed the same way platform-console's per-tenant Postgres
  pods already are today. `k8s/paas-rbac.yaml` and `k8s/network-policies.yaml` are the literal
  templates to reuse: `paas-rbac.yaml`'s per-namespace least-privilege Role/RoleBinding pattern
  (never a ClusterRole for tenant-writable resources) and `network-policies.yaml`'s
  default-deny-plus-explicit-allow pattern (its own file notes the deliberate current caveat that
  `[Ingress, Egress]` with an empty egress list blocks all egress including DNS, left for a
  later narrow `*-allow-egress-dns-istiod` policy — a ggen capsule's NetworkPolicy would need
  that same follow-up, since `sync run` needs no external network access in the base case but a
  capsule's own DNS resolution still does).
- **A receipt-volume lifecycle.** Provision, per capsule: one durable volume for
  `.ggen-v2/receipt.json` + `.ggen-v2/receipt-log.jsonl`, sized and retained independently of the
  capsule's compute lifecycle (a capsule can be torn down and recreated; its receipt history must
  not be). `k8s/resource-quotas.yaml`'s per-project quota pattern is the template for bounding
  this volume's growth per tenant.
- **A signing-key custody model.** Decide and implement where `.ggen/keys/signing.key` lives for
  a provisioned capsule — generated in-capsule on first sync (mirroring
  `crates/ggen-engine/src/keys.rs`'s existing single-machine behavior) versus injected from an
  ecosystem-level secret store. `platform-console`'s own `SONY-READINESS-GAP-CLOSURE.md` already
  flags "Secrets-at-rest encryption (envelope/KMS) for k8s Secrets" as an open IaaS-layer gap for
  the console generally; a ggen capsule's signing key inherits that same open gap and should not
  be treated as solved by this proposal.
- **A capsule-to-BRCE admission check.** Before a capsule's `sync run` is allowed to write,
  confirm receipt volume + keypair are both bound (see the invariant discussion above). No
  existing chatman-ecosystem mechanism performs this check for ggen specifically; it would be new
  code, most naturally living beside wherever the capsule provisioning API above is implemented.
- **Tenant bring-your-own ontology.** The capsule accepts a tenant-supplied `.specify/*.ttl` and
  `ggen.toml` at provisioning or mount time — IaaS does not ship, validate, or interpret ontology
  content; that is explicitly out of scope here and belongs at the PaaS layer
  (see [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md)) where marketplace packs and qualified reusable
  ontology enter the picture (`docs/51-ecosystem-map.md`'s pipeline: open-ontologies →
  ggen-marketplace → ggen).

## Rail registration

This layer would register in `catalog/rails.toml` as a new `[[rail]]` entry, standing
`CANDIDATE` rather than `ALIVE` — every existing rail in that file evidences a thing that already
runs (`constitutional_core`, `catalog`, `authority`, `evidence`, `receipts`, and others each cite
real files as `evidence`); this proposal has none yet. An illustrative shape, not a claim that
this exists:

```toml
[[rail]]
id = "ggen_iaas_capsule"
standing = "CANDIDATE"
subject = "ggen"
evidence = []  # populated once a real capsule provisioning path exists and is exercised
```

Promotion from `CANDIDATE` to `ALIVE` should require the same bar the rest of the file holds
other rails to: real evidence file paths, not narration — a real capsule that provisions, a real
receipt volume that survives capsule teardown, a real signing key that verifies a real receipt
chain end to end.

## See also

- [00-OVERVIEW](00-OVERVIEW.md) — index for this ticket set
- [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — the pack/ontology-aware layer built on top of this one
- [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — the tenant-facing product surface two layers up
- [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) — how "zero unreceipted actuation"
  applies across all three layers, not just this one
- `/Users/sac/ggen/docs/jira/v26.7.16/00-OVERVIEW.md` — the ggen-core replacement work that
  produced the receipt-chain mechanism this proposal depends on
