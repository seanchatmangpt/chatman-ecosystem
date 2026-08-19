# "Chatman Ecosystem as SMTP/TCP" — How Much Is Real Now

> **Provenance record.** Backward-chains the 2030 nanofiction vision (three candidate protocol
> primitives: hash-chained receipts, CONSTRUCT≠SELECT≠DO, OCEL v2 as a universal event wire
> format) against real, checked repo/license/artifact state as of 2026-08-19. Per the nanofiction's
> own closing coda: the *technology* pieces are separable from the *adoption-accident* premise
> (protocols win by being free and boring before the stakes are visible, not by being
> well-engineered) — this document only assesses the former, since the latter is not something
> engineering work controls.

## Verdict, stated first

**More of the precondition already holds than the nanofiction assumed.** The single biggest real
finding from checking this rather than assuming it: **`chatman-ecosystem`, `ggen-marketplace`,
and `gymact` are already public and permissively licensed (MIT/MIT/Apache-2.0)** — the "given
away" precondition the nanofiction treated as a future event is already true today for three of
the four repos this vision depends on. The one real blocker found: **`castle` is AGPL-3.0**,
a copyleft license that actively works against SMTP/TCP-style boring embedding (AGPL's
network-use clause requires any networked service using it to offer its own source — the
opposite of an unencumbered, royalty-free adoptable standard). This is a real, checked
conflict between the vision and the current repo, not a hypothetical one.

## Per-primitive assessment

### 1. Hash-chained receipts

**Real today:** `platform-console/app/lib/audit-db.ts`'s `computeRowHash`/`verifyAuditChain`,
`castle/src/v26_8_18/crypto.rs`'s dual blake3/sha256 `ArtifactIdentity` and real ML-DSA/SLH-DSA
post-quantum signature suites — both genuinely working code, not aspirational.

**Not real yet:** no standalone spec document exists. `grep`-checked: there is no
`RECEIPT-SPEC.md`, no versioned schema, no reference implementation packaged separately from
the two products (`platform-console`, `castle`) that happen to use the pattern. SMTP is a spec
(RFC 5321) with many independent implementations; today this is one pattern implemented twice,
in two different languages, with no shared contract document tying them together — the two
implementations could silently drift and nothing would catch it.

**Buildable now (days, not months):** extract a `RECEIPT-CHAIN-SPEC.md` (or a small versioned
JSON Schema) stating the real, common shape both implementations already independently arrived
at — subject/timestamp/action/prior-hash/current-hash, algorithm-agnostic — and a conformance
test either implementation can run against it. This is real, scoped engineering work, not a
research project.

### 2. CONSTRUCT ≠ SELECT ≠ DO

**Real today:** the doctrine is documented and enforced across multiple real files —
`docs/ARCHITECTURE.md`, `docs/05-non-collapse-algebra.md`, `docs/06-candidate-manufacture.md`,
`docs/jira/v26.8.18/04-GGEN-BRCE-CROSS-CUTTING.md`, and enforced in code in
`platform-console/app/lib/castle.ts` (the allowlisted-verb discipline checked directly in this
session's prior turn) and `ggen`'s pack-lifecycle contract (`pack-lifecycle.md`, checked via the
ggen-marketplace speedrun two turns ago: "Verify consequence — the consumer's native tests,
compilers, or external oracles establish whether the manufactured artifact has the required
behavior").

**Not real yet:** the doctrine exists as prose spread across several docs plus enforcement
scattered across several codebases (TypeScript in platform-console, Rust in castle, the pack
contract in ggen-marketplace) — not as one canonical, citable specification a fourth,
unaffiliated party could implement against without reading all three codebases first.

**Buildable now:** a single `CONSTRUCT-SELECT-DO.md` distilling the pattern already independently
proven correct in three real codebases into one normative document — the actual engineering
labor here is synthesis and naming precisely, not invention; the invariant already works in
production-shaped code in three places.

### 3. OCEL v2 as a universal event wire format

**Real today:** `docs/OCEL-PROCESS-EVIDENCE.md` (115 lines) documents the real
`OCEL{event_types,object_types,events,objects}` shape used by `wasm4pm-compat`
(Apache-2.0, public) and the real, checked-this-session `otel_span_to_ocel_evidence` transformer
in `ggen-marketplace/packs/otel-weaver-ocel-pack`.

**Not real yet, stated precisely — this is the weakest of the three primitives, not the
strongest:** OCEL v2 itself is an existing external open standard
(process-mining community, not invented here) — so "chatman-ecosystem as OCEL's SMTP" would mean
being a *reference implementation* of someone else's protocol, not originating a new one, which
is a materially different and smaller claim than the nanofiction's framing implied. Checked this
session (the OTEL→Weaver→OCEL plan's own verification criteria): the pipeline from real telemetry
to a real, continuously-growing OCEL log has real consumers built (the accumulator, the
discovery bridge) but has not been exercised by any party outside this codebase — "universal
wire format" requires a second, independent, unaffiliated implementation actually consuming it,
and none exists yet.

**Buildable now:** publish the transformer's output contract (the exact OCEL v2 JSON shape this
codebase emits, byte-for-byte, from a real captured example) as a standalone fixture + schema in
a public repo, so an external party could write a consumer against it without needing to read
this codebase's internals — the emission side is real; a documented, external-facing contract
for it is not, yet.

## What actually blocks the vision that engineering work does not fix

Named plainly, in the same register as the payment-processor and marketplace-review docs before
this one: an adoption-accident (being free, boring, and first through the door before anyone
realizes the stakes) is not a controllable engineering output. Three of four core repos are
already unencumbered — that part of the precondition holds today, checked, not assumed. The
fourth (`castle`, AGPL-3.0) actively works against it and would need a real relicensing decision
before any "given away as infrastructure" story could include it — that decision is the
project owner's to make, not a code change.

## Summary table

| Primitive | Working code exists | Standalone spec exists | License allows "boring ubiquity" | Real buildable-now item |
|---|---|---|---|---|
| Hash-chained receipts | Yes (2 langs) | No | Yes (both host repos MIT/Apache) | `RECEIPT-CHAIN-SPEC.md` + conformance test |
| CONSTRUCT≠SELECT≠DO | Yes (3 codebases) | No (prose, scattered) | Mixed — castle is AGPL | `CONSTRUCT-SELECT-DO.md` normative doc |
| OCEL v2 emission | Yes (real transformer + accumulator) | Partial (`OCEL-PROCESS-EVIDENCE.md`) | Yes (wasm4pm-compat Apache-2.0) | Published fixture + schema for external consumers |
| Overall "given away" precondition | — | — | 3 of 4 repos already public+permissive; castle (AGPL) is the real, checked exception | A relicensing decision on castle, if it's meant to carry this role |
