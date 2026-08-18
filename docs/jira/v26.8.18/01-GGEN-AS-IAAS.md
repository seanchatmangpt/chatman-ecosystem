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

`CONSTITUTION.md`'s governing equation is `A = μ(O*)` (admitted observation to lawful
manufacture to artifact-with-evidence-backed-standing), under law 1, "Zero unreceipted
actuation," and law 2, "Broker-only DO. Adapters submit intentions; the authority broker
decides whether an actuation is lawful" — the mechanism this repo names BRCE elsewhere
(`docs/09-brce-no-unreceipted-actuation.md`). At the
PaaS and SaaS layers a tenant interacts through a curated surface (a pack registry, a console, an
API) that can mediate every write. At the IaaS layer, by construction, a tenant has raw access to
ggen's own Write stage — the fifth stage of the sync pipeline that actually touches the
filesystem. That is precisely the point where "zero unreceipted actuation" is easiest to violate
by omission: a tenant capsule that lets `sync run` execute without a receipt volume mounted, or
without signing keys provisioned, produces real filesystem mutation with no admissible evidence
trail — the exact failure mode `docs/10-receipt-bifurcation.md` names ("Receipt validation
should reject any attempt to satisfy BRCE with a derivation receipt") and the exact failure
mode ggen's own `docs/jira/v26.7.16/` receipt-chain work exists to
prevent inside the ggen repo. An IaaS layer that provisions compute without provisioning receipt
custody as a co-equal, non-optional resource would reintroduce that gap at the ecosystem boundary
even though ggen itself already closes it internally.

Concretely, this means the IaaS provisioning contract cannot treat the receipt volume as optional
storage a tenant might attach later — the capsule's own admission gate should refuse to start
`sync run` at all if no receipt volume and no keypair are bound, mirroring
`crates/ggen-engine/src/keys.rs`'s own behavior (generate-on-first-sync) but applied at the
capsule boundary instead of inside a single binary invocation.

## What would need to be built (concrete, greenfield)

Status as of this pass, checked against the real files, not the other tickets' prose:

- **A capsule provisioning API — done at the process level, still one shared process, not one
  capsule per tenant.** `platform-console/services/ggen/app.py` (560 lines) has a real
  `POST /provision` endpoint (not the illustrative `POST /iaas/ggen/capsules` shape below, but
  the same real substance): it shells out to the real `ggen` binary (`run_ggen`,
  `subprocess.run`), runs the real `ggen init` → ontology write → `ggen packs install` →
  `ggen sync run` sequence (`provision()`/`_provision_inner()`, `app.py:312-481`), and returns
  the real BLAKE3-chained, ed25519-signed receipt plus an independent `ggen receipt verify`
  result inline in the response (`receipt_verification.result`) — this was independently
  verified this session (`signature_valid: true`). Since this ticket was first drafted,
  per-tenant scoping has landed: `/provision` now requires a `project` field, and
  `resolve_tenant_namespace()` (`app.py:214-236`) picks or provisions a real Kubernetes
  namespace for it via `k8s_request()`'s in-cluster ServiceAccount HTTPS client, with each
  run directory nested under `WORKSPACE_ROOT/<namespace>/run-<uuid>` instead of one shared
  flat run directory. What remains open: this is a namespace-scoped run directory inside one
  still-shared service process, not a separate pod/capsule per tenant, and there is still no
  `paas-rbac.yaml`/`network-policies.yaml` RoleBinding/NetworkPolicy scoping that namespace to
  a single tenant's capsule the way those two files already do for other per-tenant workloads.
  `k8s/services-and-deployments.yaml:489` now points the `ggen-status` Deployment at
  `image: platform-console/ggen-status:v26.8.18-live` (no longer `:latest`), so the manifest has
  been updated toward the new `/provision` code — but this pass could not reach a live cluster
  (`kubectl get pods -n ggen` timed out) to confirm the pod is actually running that image.
  State this precisely: the provisioning logic is real, tenant-namespace-scoped, and verified
  locally; the manifest now targets a rebuilt image; actual live-pod confirmation is unverified.
- **A receipt-volume lifecycle — still open.** `app.py` writes receipts under
  `WORKSPACE_ROOT` (`/app/state/runs/run-<uuid>/.ggen-v2/receipt.json` +
  `receipt-log.jsonl`), and the module's own docstring states plainly that no PersistentVolume
  backs `/app/state` for this Deployment today, so a pod restart loses all prior run receipts —
  this is the same gap the ticket originally named, not yet closed. The per-project managed-addon
  precedent that landed this session (`platform-console/app/lib/redis.ts`'s
  `provisionProjectRedis` and `platform-console/app/lib/queue.ts`'s `provisionProjectQueue`, each
  a real Deployment+Service+NetworkPolicy+Secret provisioned per project) is a real, closer
  template for a future receipt volume than `k8s/resource-quotas.yaml` alone — but neither module
  provisions a PVC (both explicitly use `emptyDir`/no volume, per their own doc comments), so
  durable per-tenant receipt storage remains unbuilt.
- **A signing-key custody model — partially done.** `app.py`'s `resolve_signing_key()`
  (`app.py:251-269`) implements a real, working precedence — `GGEN_SIGNING_KEY` env var if the
  operator injected one, else a previously-generated key at `SIGNING_KEY_PATH`, else a freshly
  generated `secrets.token_hex(32)` seed persisted with `0o600` perms — resolved once at process
  start and exported into every `ggen` subprocess's environment. This is a real decision and a
  real implementation, not illustrative. What remains open, and is disclosed in the module's own
  docstring rather than hidden: `SIGNING_KEY_PATH` has no PersistentVolume backing it either, so
  a pod restart mints a new key and orphans receipts signed under the old one; wiring a PVC or a
  real k8s Secret is still needed for production durability.  `SONY-READINESS-GAP-CLOSURE.md`'s
  "Secrets-at-rest encryption (envelope/KMS) for k8s Secrets" gap still applies unchanged.
- **A capsule-to-BRCE admission check — still open.** `_provision_inner()` refuses to run only
  when the `ggen` binary itself is missing (`app.py:354-361`, a real 503 refusal, not a
  synthesized "ok") or when tenant-namespace resolution fails (`app.py:371-379`, a real 502
  refusal); it does not refuse when the receipt volume is non-durable or when the signing key was
  just freshly minted rather than operator-provisioned — both conditions the invariant discussion
  above says should gate `sync run`. No such admission check exists yet.
- **Tenant bring-your-own ontology — done, in the per-tenant form this layer needs.**
  `/provision`'s request body already carries a caller-supplied `ontology` string, written
  verbatim to `run_dir / "schema" / "domain.ttl"` before `sync run` (`app.py:402-404`), inside
  the now-tenant-namespaced `run_dir` described above — the service does not validate or
  interpret its content, matching the ticket's original scope split (IaaS accepts; PaaS/SaaS
  validate and curate, see [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md)).

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
