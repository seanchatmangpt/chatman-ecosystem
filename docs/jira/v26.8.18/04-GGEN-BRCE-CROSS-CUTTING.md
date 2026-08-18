# 04 — The BRCE Invariant Across IaaS/PaaS/SaaS ggen

Part of [00-OVERVIEW](00-OVERVIEW.md), read alongside [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md),
[02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md), and [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md). Those three
tickets propose a layer each; this one argues the layers are not three products but three
different actuation-authority boundaries wrapped around one core, and names the single invariant
none of them may opt out of: `CONSTITUTION.md`'s "Zero unreceipted actuation" — the broker (BRCE)
is the only lawful DO path, everything else may only submit intentions, and the governing
equation `A = mu(O*)`, `R = receipt(A)` binds admitted observation to lawful manufacture to
artifact to receipt at every scale this repository recognizes.

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

`CONSTITUTION.md` draws a load-bearing distinction: "Derivation receipt != Actuation receipt."
A derivation receipt attests that a computation happened; an actuation receipt attests that a
real-world mutation happened through the one lawful DO path. This distinction sharpens, not
blurs, as the layers stack:

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
  this dispatcher, just crossing a tenant boundary instead of a single project's working tree; no
  existing analogue in this repo crosses that boundary today, but the receipt-tagging discipline
  the dispatcher already proves is the correct model to extend.
- **SaaS.** The actuation receipt is not a byproduct of the product, it is the product. A
  capability purchased one-click has no other deliverable that satisfies "zero unreceipted
  actuation" — the receipt itself is what the buyer is buying proof of having received.

## Registering each layer as its own rail

`catalog/rails.toml` names 19 rails today (`constitutional_core`, `catalog`, `authority`,
`evidence`, `receipts`, `projection`, `cli`, `storage_sqlx`, `mcp_boundary`,
`gall_checkpoints`, and others), each carrying a real standing value
(ALIVE/CANDIDATE/REJECTED/PARTIAL_ALIVE) backed by cited evidence files. ggen itself is already
tracked this way at the repository level: `status/repos/ggen.md` pins it at
`main@162e466d8f07`, role `manufacture`, standing `PARTIAL_ALIVE`, and `status/snapshot.json` is
the canonical fleet-status view that standing rolls up into. A layered ggen implies three
candidate rails — `ggen_iaas`, `ggen_paas`, `ggen_saas` — each with its own standing, not one
rail inherited wholesale from the repo-level `PARTIAL_ALIVE` pin. This matters because the three
layers will not mature at the same rate or on the same evidence: IaaS-layer receipt mechanics are
already substantially real (the sync pipeline, the receipt chain, `ggen receipt verify`); PaaS-
and SaaS-layer actuation across tenant boundaries has no existing analogue and would enter the
catalog at `CANDIDATE`, not `PARTIAL_ALIVE`, until it can cite its own evidence files the way the
19 existing rails do.

## OCEL v2 as the shared process vocabulary

`docs/39-process-is-state.md`'s "Process as State: OCEL v2 and the Collapse of
Workflow/Data Separation" is not a proposed integration point for a layered ggen — it is a real
point of kinship that already exists. ggen's own `crates/ggen-graph/ocel/pack_events.rs` emits
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
same:

- **IaaS.** A real receipt round-trip demonstrated end to end: `ggen sync run` producing a
  chained `.ggen-v2/receipt.json`, followed by a real `ggen receipt verify` pass against that
  same receipt — this loop already exists and is the evidence bar, not a proposal.
- **PaaS.** A real BRCE-gated write demonstrated crossing a tenant boundary: an
  `unattended_dispatch`-style write with `origin = "unattended-dispatch"` (or an equivalent
  tenant-scoped origin tag) landing in a provisioned tenant environment, with the corresponding
  entry appearing in a durable attempt log the same way `.ggen/unattended-dispatch-log.jsonl`
  already logs every attempt, success or failure.
- **SaaS.** A real capability-purchase-to-actuation-receipt path demonstrated: a purchase event
  resolving to one concrete actuation receipt the buyer can independently verify, with a hard
  refusal (not a warning) at any trust-tier boundary the purchase would otherwise cross, mirroring
  `verify_trust_tier`'s existing `Err`-not-warning discipline.

Until each of those three demonstrations exists and is cited the way `catalog/rails.toml`'s
existing 19 rails cite their own evidence files, the honest standing for `ggen_paas` and
`ggen_saas` is `CANDIDATE`. `ggen_iaas` can plausibly enter at `PARTIAL_ALIVE`, matching ggen's
own repo-level pin in `status/repos/ggen.md`, on the strength of the sync/receipt loop that
already exists — but even that requires the rail's own evidence citation, not an inherited
assumption from the repo-level standing.

## See Also

- [00-OVERVIEW](00-OVERVIEW.md) — index for this ticket set
- [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — the derivation-receipt-heavy foundation layer
- [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — where actuation receipts first cross a tenant boundary
- [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — where the actuation receipt becomes the delivered product
- `/Users/sac/chatman-ecosystem/CONSTITUTION.md` — "Zero unreceipted actuation," BRCE, `A = mu(O*)`
- `/Users/sac/chatman-ecosystem/docs/39-process-is-state.md` — OCEL v2 as constitutional primitive
