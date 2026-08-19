# ce-receipt/1 — Receiptability as an Admission Precondition, Not a Log Line

> Status: draft, fragment of the `ce-*` protocol family (DfCM inversion, 2026-08-19).
> Independently versioned; see [`07-CE-AUTHORITY-1.md`](07-CE-AUTHORITY-1.md) for the sibling
> fragment this one composes with.

## The claim this fragment formalizes

> Do not think `Action → Receipt`. Think: no receipt-capable consequence path ⇒ no
> consequential action. Receiptability becomes an admission precondition.

Formally, BRCE becomes `Intent → Authority → ReceiptCapability → Actuation →
ObservedConsequence → Receipt → Replay`, not "do something and log it."

## Checked against real code

### Where the un-inverted "do something and log it" shape still holds

`platform-console/app/middleware.ts`'s per-request audit write (round 9's `orgId` sweep target)
calls `writeAuditLogEntry` **after** the request has already been processed — the write is a
side effect appended post-hoc, not a precondition the request had to pass through to be admitted
in the first place. If the write failed, nothing in the request path today refuses the action
retroactively; the action already happened. This is `Action → Receipt`, exactly the shape the
inversion names as the thing to invert.

### Where `ReceiptCapability` as a real precondition already exists

`~/castle/src/castle.rs`'s header names "the receipted CONSTRUCT admission chain" directly —
checked, not inferred from the comment alone: `~/castle/tests/dfcm_full_closure.rs`'s
`CastleCellManifest` struct requires `local_receipt_store: "receipt://aws-test"` as a mandatory
field of every deployment cell *before* any `max_parallel_do` is even declared — a cell with no
receipt store configured cannot be constructed as a valid manifest at all. This is real
`ReceiptCapability` gating construction, not appended after.

`platform-console/app/lib/audit-db.ts`'s hash chain (`computeRowHash`, `verifyAuditChain`)
provides the `Receipt`/`Replay` end of the chain for real — every row commits to its predecessor,
and `verifyAuditChain()` can detect a broken link. But this verifies receipts *after* they were
written; it does not currently gate whether the originating action was allowed to proceed absent
a working receipt path.

## What `ce-receipt/1` conformance actually requires

1. Before any `Actuation` step runs, the implementation checks that a `ReceiptCapability` exists
   and is reachable (a configured, live receipt store — not merely "receipt writing code
   exists somewhere in the binary").
2. If `ReceiptCapability` is unreachable, `Actuation` is refused, not attempted-then-logged.
3. `ObservedConsequence` (the real, checked result of the actuation, not the intended one) is
   what gets receipted — `castle`'s crypto module computing a real `blake3`/`sha256` digest of
   actual output bytes, not of the request that asked for the output, is the right shape here.
4. `Replay` must be possible from the receipt chain alone, without re-deriving the action from
   application logs outside the chain.

## Real, scoped gap

`platform-console`'s HTTP-route-level actions (the ~95-file `orgId` sweep from round 9-10) do
not conform: they write after acting, and a `writeAuditLogEntry` failure does not unwind or
refuse the already-completed action. `castle`'s cell-manifest construction is closer to
conformant for its own narrow domain (a manifest without a receipt store cannot be constructed),
but this has not been checked against whether `castle`'s actual `DO` execution path — not just
manifest validation — enforces the same precondition at actuation time, only at manifest-
construction time. That check is a real, scoped follow-up, not claimed done here.

## Explicit non-claims

- `platform-console`'s route layer does not conform to `ce-receipt/1` today.
- `castle`'s manifest-construction-time enforcement is real; its actuation-time enforcement is
  unverified in this pass, not confirmed absent.
- No external party has reviewed or ratified this fragment.
