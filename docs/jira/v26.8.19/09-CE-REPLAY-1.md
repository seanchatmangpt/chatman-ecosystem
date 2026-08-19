# ce-replay/1 — Replay From the Receipt Chain Alone

> Status: draft, fragment of the `ce-*` protocol family. Terminal step of
> [`06-CE-RECEIPT-1.md`](06-CE-RECEIPT-1.md)'s `Intent → Authority → ReceiptCapability →
> Actuation → ObservedConsequence → Receipt → Replay` chain.

## The claim this fragment formalizes

A consequence's receipt must be sufficient, on its own, to reconstruct or re-verify what
happened — without needing to re-read application logs, re-run the original code path, or trust
the actor's own account of the action.

## Checked against real code

`platform-console/app/lib/audit-db.ts`'s `verifyAuditChain()` is the real, working candidate for
this fragment on the `platform-console` side: it walks the hash chain and detects breakage
independent of the application code that originally wrote the rows — a real replay-shaped
verification, not a trust-the-writer check. `backfillAuditLogChain` (same file) additionally
proves the chain can be *reconstructed* from row content forward, which is closer to `ce-replay`'s
requirement than mere tamper-detection.

`~/castle/tests/dfcm_full_closure.rs`'s `CastleCellManifest` requires `local_ocel_store:
"ocel://aws-test"` as a mandatory field alongside `local_receipt_store` — meaning `castle`'s own
model treats the OCEL process trace as co-equal, mandatory infrastructure alongside the receipt
store itself, not an optional add-on. This matters for replay specifically: a receipt proves an
event happened and wasn't tampered with; an OCEL trace is what lets a third party reconstruct
the *process* the receipted events were steps of — the difference between "this happened" and
"this is how it happened, in order, related to these other events."

## What `ce-replay/1` conformance actually requires

1. A verifier holding only the receipt chain (no access to the original application's database,
   logs, or source) can determine whether a claimed sequence of consequences is internally
   consistent.
2. The receipt chain, combined with the OCEL trace it's paired with (per `castle`'s own
   mandatory-field discipline), is sufficient to reconstruct event ordering and object
   relationships, not just individual event validity.
3. `verifyAuditChain`-shaped functions must be runnable by a party who did not write the rows —
   checked here only for the same-codebase case; cross-party replay (a genuinely external
   verifier) has not been exercised.

## Real, scoped gap

`verifyAuditChain()` has only ever been run by `platform-console`'s own code, against its own
database, in this session — real, but not yet the cross-party case `ce-replay/1` is ultimately
for. No test exists (checked: no dedicated replay-fixture file found under
`platform-console/app` or `castle/tests`) exporting a receipt chain + OCEL trace pair as a
standalone artifact an unrelated process could independently verify without any shared code.
That artifact — a real exported fixture plus a minimal, dependency-free verifier — is the
concrete next step this fragment names but does not build.

## Explicit non-claims

- Same-codebase chain verification is real and working; cross-party replay is unverified, not
  confirmed absent — it has simply not been attempted.
- No external party has reviewed or ratified this fragment.
