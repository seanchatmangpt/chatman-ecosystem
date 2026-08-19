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

**Update (2026-08-19): the standalone-artifact gap named below is now closed; cross-party live
export is not.** Two new scripts exist:
`platform-console/scripts/export-replay-fixture.ts`, which issues a real query against
`platform_console.audit_log` via `lib/audit-db.ts`'s `getAuditDbPool()` and exports the most
recent N rows chain-ordered to JSON, failing closed (nonzero exit, no file written) if no
database is reachable rather than fabricating rows; and
`platform-console/scripts/verify-replay-fixture.ts`, a genuinely dependency-free verifier
(confirmed by grep: only `node:crypto`/`node:fs` imports, zero imports from `audit-db.ts` or any
app code) that independently re-derives the sha256 row-hash chain from the fixture's own
self-documented algorithm spec.

No live cluster/database was reachable in this environment, so `export-replay-fixture.ts` has
only been exercised on its fail-closed path (confirmed: exit 1, no file written, no in-cluster
credentials found). The committed fixture at `platform-console/scripts/fixtures/replay-fixture-sample.json`
is therefore **hand-constructed, not a live export** — its 20 rows' actor/path/timestamp content
is synthetic — but its hash chain is real, computed with a standalone re-implementation of
`audit-db.ts`'s exact `computeRowHash` algorithm, and the fixture's own `source.note` field
documents this rather than implying a live export. Running the verifier against it produced real
output: `VALID: 20 row(s) verified, hash chain intact from genesis through row 20`, exit 0.
Adversarially tampering one row's `actor` field in a copy and re-running produced `INVALID: row
11: recomputed row_hash (...) does not match the stored row_hash (...)`, exit 1 — confirming the
verifier actually detects tampering, not just echoes success.

This closes conformance requirement 1's *artifact* gap (a standalone fixture + dependency-free
verifier now exist) but does not close the cross-party case itself: no unrelated process/party
has actually run the verifier independent of this session, and `export-replay-fixture.ts`'s live
(non-fail-closed) path remains untested against a real cluster. The fixture also only carries the
subset of chain-committed fields `verifyAuditChain` reads
(`request_id/ts/actor/method/path/status/castle_receipt_digest/impersonated_by/impersonation_session_id`)
— rows chain-committing `org_id/key_id/duration_ms/sla_credit_*` would not reverify from this
narrower fixture format alone, documented in the fixture's own `hashAlgorithm.material` field.
Requirement 2 (OCEL trace pairing per `castle`'s mandatory-field discipline) remains entirely
unaddressed — the new fixture carries only the receipt-chain half, no OCEL trace.

## Explicit non-claims

- Same-codebase chain verification is real and working; cross-party replay is unverified, not
  confirmed absent — it has simply not been attempted.
- No external party has reviewed or ratified this fragment.
