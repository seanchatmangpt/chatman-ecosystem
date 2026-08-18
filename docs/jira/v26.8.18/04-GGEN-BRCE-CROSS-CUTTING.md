# 04 — The BRCE Invariant Across IaaS/PaaS/SaaS ggen

Part of [00-OVERVIEW](00-OVERVIEW.md), read alongside [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md),
[02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md), and [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md). Those three
tickets propose a layer each; this one argues the layers are not three products but three
different actuation-authority boundaries wrapped around one core, and names the single invariant
none of them may opt out of: `CONSTITUTION.md`'s law 1, "Zero unreceipted actuation," and law 2,
"Broker-only DO. Adapters submit intentions; the authority broker decides whether an actuation
is lawful" — the mechanism this ecosystem names BRCE in `docs/09-brce-no-unreceipted-actuation.md`
— and the governing equation `A = μ(O*)` binds admitted observation to lawful manufacture to
artifact-with-evidence-backed-standing at every scale this repository recognizes.

## Why layering does not relax the invariant

`CONSTITUTION.md` states the repository "governs identities, relationships, policies, evidence,
and standing across independently releasable projects. It is a control plane, not a source-code
monorepo." A control plane does not get to loosen its own core rule per surface area — the
invariant is stated once, at the constitutional layer, precisely so IaaS/PaaS/SaaS framing
(a deployment-topology concern) cannot be read as also being an authority-scope concern. An IaaS
ggen still cannot write a file without a receipt: `crates/ggen-engine/src/sync.rs`'s five-stage
pipeline (Resolve → Enrich → Extract → Render → Write) already terminates in a receipted write
today, via `crates/praxis-core/src/receipt_record.rs`'s `ReceiptRecord` chained through BLAKE3 to
`.ggen-v2/receipt.json`/`receipt-log.jsonl`. A PaaS ggen's managed pipeline still cannot skip
verification — the same receipt chain is the only mechanism a managed pipeline has for proving it
ran the pipeline it claims to have run. A SaaS ggen's one-click capability purchase still has to
produce a real, replayable receipt as the delivered trust artifact, because in this ecosystem a
receipt is not a log line, it is the product's proof of having happened at all.

## Derivation receipts vs. actuation receipts, mapped onto the three layers

`docs/10-receipt-bifurcation.md` draws a load-bearing distinction this ecosystem's constitution
implies but does not itself spell out in those words: "Receipt validation should reject any
attempt to satisfy BRCE with a derivation receipt, even when the underlying semantic artifact is
perfectly valid." A derivation receipt attests that a computation happened; an actuation receipt
attests that a real-world mutation happened through the one lawful DO path
(`CONSTITUTION.md` law 2, "Broker-only DO"). This distinction sharpens, not blurs, as the layers
stack:

- **IaaS.** Most receipts in play are pure derivation — the sync pipeline's internal stage
  transitions (`pipeline.load`/`extract`/`validate`/`generate`/`emit`, per the OTEL contract
  ggen's own workspace `CLAUDE.md` documents) are computed facts about what the pipeline did to
  its own graph state, not yet claims about a tenant's world changing.
- **PaaS.** The developer-facing "deploy" action is where a derivation receipt has to become an
  actuation receipt — a write actually lands in a tenant's environment. Ggen already has the
  closest existing model for this narrow jump: the Bounded Unattended-Write Dispatcher
  (`ggen-mcp`'s `unattended_dispatch::try_unattended_apply`, documented in ggen's own workspace
  `CLAUDE.md`), which tags every such write in its own receipt with
  `ReceiptRecord::origin = "unattended-dispatch"` and logs the attempt — success or failure — to
  `.ggen/unattended-dispatch-log.jsonl` every time, not only on success. A PaaS-scale "managed
  pipeline runs and deploys without a human clicking confirm" is structurally the same shape as
  this dispatcher, just crossing a tenant boundary instead of a single project's working tree.
  Since this ticket was written, `platform-console/services/ggen/app.py`'s `/provision`
  endpoint has become a real (if partial) instance of exactly this crossing — it resolves a
  real per-tenant Kubernetes namespace, tags its response with a BRCE-style origin, and logs
  every attempt to a durable JSONL file — modeled on, though not identical to, the dispatcher's
  own `origin = "unattended-dispatch"` receipt-tagging discipline (see the PaaS evidence bullet
  below for the exact gaps still open).
- **SaaS.** The actuation receipt is not a byproduct of the product, it is the product. A
  capability purchased one-click has no other deliverable that satisfies "zero unreceipted
  actuation" — the receipt itself is what the buyer is buying proof of having received.

## Registering each layer as its own rail

`catalog/rails.toml` names 21 rails today (`constitutional_core`, `catalog`, `authority`,
`evidence`, `receipts`, `projection`, `cli`, `storage_sqlx`, `mcp_boundary`,
`gall_checkpoints`, `release_admission`, `ggen`, and others), each carrying a real standing
value (ALIVE/CANDIDATE/REJECTED/PARTIAL_ALIVE) backed by cited evidence files. ggen itself is
now tracked two ways at once: at the repository level, `status/repos/ggen.md` pins it at
`main@162e466d8f07`, role `manufacture`, standing `PARTIAL_ALIVE` (rendered from
`status/snapshot.json`, the canonical fleet-status view that standing rolls up into); and, since
this ticket was written, `catalog/rails.toml` also now carries a single `id = "ggen"` rail at
`PARTIAL_ALIVE`, evidencing `platform-console/services/ggen/app.py` and
`docs/jira/v26.8.18/02-GGEN-AS-PAAS.md`. A layered ggen still implies three candidate rails —
`ggen_iaas`, `ggen_paas`, `ggen_saas` — each with its own standing, distinct from both the
repo-level pin and the new single `ggen` rail, which conflates layers that have not equally
matured. This matters because the three layers will not mature at the same rate or on the same
evidence: IaaS-layer receipt mechanics are already substantially real (the sync pipeline, the
receipt chain, `ggen receipt verify`, and now a real HTTP `/provision` endpoint exercising all
of it); PaaS-layer tenant-namespace actuation is now also real (see the PaaS bullet below);
SaaS-layer actuation across a purchase/fulfillment boundary has no existing analogue and would
enter the catalog at `CANDIDATE`, not `PARTIAL_ALIVE`, until it can cite its own evidence files
the way the other existing rails do.

## OCEL v2 as the shared process vocabulary

`docs/39-process-is-state.md`'s "Process as State: OCEL v2 and the Collapse of
Workflow/Data Separation" is not a proposed integration point for a layered ggen — it is a real
point of kinship that already exists. ggen's own `crates/ggen-graph/src/ocel/pack_events.rs` emits
OCEL events today. Any of the three layers that need to describe "what happened, to what object,
in what order" (a tenant's deploy history at PaaS, a purchased capability's fulfillment lifecycle
at SaaS) can project into the same OCEL v2 event vocabulary the ecosystem's constitution already
treats as a first-class primitive, instead of inventing a parallel process-log format per layer.
This is the natural shared substrate underneath the receipt chain: receipts prove a mutation was
lawful and hashed; OCEL events describe the process that produced it. The two are complementary,
not competing, records.

## Trust-tier enforcement as the precedent for authority boundaries

`crates/ggen-marketplace/src/marketplace/install.rs`'s `verify_trust_tier` (consulting
`profile.rs`/`trust.rs`) is today's concrete precedent for how this ecosystem enforces authority
boundaries around a shared capability surface: it returns a real `Err`, not a logged warning, per
`.claude/rules/coding-agent-mistakes.md`'s Fail-Open Behavior mistake class in ggen's own repo —
a violated trust tier stops the install, it does not merely note the violation. This is exactly
the discipline a layered ggen needs to extend past pack trust tiers into tenant/capability trust
tiers: at PaaS, a tenant's pipeline should not be able to actuate a write class its trust tier
does not admit; at SaaS, a capability purchase should not fulfill against a trust tier the buyer
has not cleared. The mechanism generalizes — `verify_trust_tier`'s pattern of "hard refusal, not
soft warning" is the one this ecosystem already trusts, and a layered ggen should reuse the
pattern rather than inventing a second, weaker authority check at the tenant boundary.

## What moves a unified ggen ecosystem rail from CANDIDATE to ALIVE

Concrete, per-layer evidence — not narrative — is what the existing rails in
`catalog/rails.toml` require, and a `ggen_iaas`/`ggen_paas`/`ggen_saas` rail set would need the
same. Since this ticket was written, `platform-console/services/ggen/app.py` gained a real
`POST /provision` endpoint; the status below is checked against that file directly, not against
this ticket set's own earlier prose.

- **IaaS.** A real receipt round-trip demonstrated end to end: `ggen sync run` producing a
  chained `.ggen-v2/receipt.json`, followed by a real `ggen receipt verify` pass against that
  same receipt — this loop already exists and is the evidence bar, not a proposal. **DONE**,
  and now also exercised from outside the CLI: `platform-console/services/ggen/app.py`'s
  `provision()` shells out to the real `ggen` binary (`init` → `packs install` → `sync run` →
  `receipt verify`, all via real `subprocess.run`, per that file's own "Nothing here is
  simulated" doc comment) and returns the real chained, BLAKE3-hashed, ed25519-signed
  `ReceiptRecord`, independently verified (`signature_valid: true`) in this session.
  `platform-console/k8s/services-and-deployments.yaml:489` now points the `ggen-status`
  Deployment at `image: platform-console/ggen-status:v26.8.18-live` (no longer `:latest`), so
  the committed manifest targets the rebuilt image — but this pass could not reach a live
  cluster (`kubectl get pods -n ggen` timed out) to confirm the running pod is actually serving
  it. The IaaS receipt loop is real and callable over HTTP in the built service and the
  manifest now points at it; whether it is live in production is unverified in this pass, not
  confirmed either way.
- **PaaS.** A real BRCE-gated write demonstrated crossing a tenant boundary: a write tagged
  with a BRCE-style origin landing in a provisioned tenant environment, with the corresponding
  entry appearing in a durable attempt log the same way `.ggen/unattended-dispatch-log.jsonl`
  already logs every attempt, success or failure. **DONE, at the process level; not yet a
  separate per-tenant capsule.** `app.py`'s `/provision` no longer runs inside one flat shared
  `WORKSPACE_ROOT` run directory — it now resolves a real per-tenant Kubernetes namespace via
  `resolve_tenant_namespace()` (`app.py:214-236`, using the same `k8sRequest`-based in-cluster
  pattern `redis.ts`/`queue.ts` already use), nests the run under
  `WORKSPACE_ROOT/<namespace>/run-<uuid>`, tags every response `"origin":
  "ggen-paas-provision"` (`app.py:92,469`, distinct from but modeled on
  `unattended_dispatch.rs`'s `origin = "unattended-dispatch"` convention), and appends one JSON
  line per attempt — `applied` or `refused_or_error`, success or failure — to
  `PROVISION_LOG_PATH` (`append_provision_log()`, `app.py:238-249`), the same "log every
  attempt" discipline `.ggen/unattended-dispatch-log.jsonl` uses. The prior grep-confirmed claim
  that no `origin`/`unattended-dispatch` string appears in `app.py` no longer holds — both now
  appear, repeatedly. What remains open: this is one shared service process picking a tenant
  namespace per request, not an isolated per-tenant pod/capsule (see
  [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md)); the receipt volume and the attempt log both live on
  the pod's local `emptyDir` (no PVC), so they do not survive a pod restart; and the receipt's
  own signed bytes still carry `origin: null` (the CLI has no `--receipt-origin` flag) — only
  the HTTP response envelope is tagged, disclosed honestly in the module's own docstring rather
  than forged into the signed receipt.
- **SaaS.** A real capability-purchase-to-actuation-receipt path demonstrated: a purchase event
  resolving to one concrete actuation receipt the buyer can independently verify, with a hard
  refusal (not a warning) at any trust-tier boundary the purchase would otherwise cross, mirroring
  `verify_trust_tier`'s existing `Err`-not-warning discipline. **Still open** — no purchase/
  fulfillment path exists in `platform-console/services/ggen/app.py` or elsewhere in this
  session's changes; `/provision` has no caller-facing purchase or entitlement concept, only an
  ontology/packs request body.

Since this was written, `catalog/rails.toml` has in fact gained a ggen rail — but as one
repo-level entry (`id = "ggen"`, `standing = "PARTIAL_ALIVE"`, `evidence = [
"platform-console/services/ggen/app.py", "docs/jira/v26.8.18/02-GGEN-AS-PAAS.md"]`), not the
three-way `ggen_iaas`/`ggen_paas`/`ggen_saas` split this ticket proposes. That single rail's
`PARTIAL_ALIVE` standing is defensible for the IaaS-level receipt loop and for the
PaaS-level tenant-namespace/origin/attempt-log mechanics described above (both real,
independently verified, still not confirmed live in a running cluster as of 2026-08-18 — a
verification attempt against `kind-platform-eng-colima` found `docker ps` reporting the kind
control-plane container up, but `kubectl get nodes` failing with a TLS handshake timeout on two
retries; the cluster's API server was unreachable and no build/load/apply/curl verification could
be performed, so standing remains `PARTIAL_ALIVE` on code-level evidence alone, not live-cluster
evidence), but it is not yet
defensible for the SaaS layer, which has no capability-purchase or catalog surface at all — a
single undifferentiated `PARTIAL_ALIVE` rail risks reading as covering all three layers when
only two have any real evidence. The per-layer split this ticket proposes remains the more
honest shape: it would let `ggen_iaas` and `ggen_paas` carry their own real, cited evidence
while `ggen_saas` stays `CANDIDATE` until a real purchase/fulfillment path exists — rather than
one rail's `PARTIAL_ALIVE` standing being read as covering ground it does not yet cover.

## See Also

- [00-OVERVIEW](00-OVERVIEW.md) — index for this ticket set
- [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — the derivation-receipt-heavy foundation layer
- [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — where actuation receipts first cross a tenant boundary
- [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — where the actuation receipt becomes the delivered product
- `/Users/sac/chatman-ecosystem/CONSTITUTION.md` — "Zero unreceipted actuation," BRCE, `A = mu(O*)`
- `/Users/sac/chatman-ecosystem/docs/39-process-is-state.md` — OCEL v2 as constitutional primitive
