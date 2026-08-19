# ce-standing/1 — A Shared, Closed Vocabulary for What a Claim's Evidence State Is

> Status: draft, fragment of the `ce-*` protocol family.

## The claim this fragment formalizes

For "Foreign implementations passing Chatman conformance" to mean anything comparable across
implementations, the *vocabulary* for reporting a claim's evidence state must be shared and
closed — not each implementation inventing its own ad hoc "works"/"partial"/"broken" labels that
don't map onto each other.

## Checked against real code — this already exists, independently, in two places

`~/castle/src/v26_8_18/topology.rs:38-46`, a real, shipped, closed enum:

```rust
pub enum ReleaseStanding {
    Unknown, PartialAlive, Alive, Blocked, BuildBroken, Unsupported, Refused,
}
```

Separately, and without direct code sharing, this session's own working vocabulary (established
in `~/.claude/rules/no-overclaiming-rust.md`, applied throughout this session's docs) uses
`ALIVE/PARTIAL/BLOCKED/MOCKED/REFUSED/UNSUPPORTED/UNVERIFIED` — six of seven terms overlap with
`castle`'s real enum almost exactly (`PartialAlive`≈`PARTIAL`, `Blocked`≈`BLOCKED`,
`BuildBroken`≈closest to `MOCKED`-adjacent-but-distinct, `Refused`≈`REFUSED`,
`Unsupported`≈`UNSUPPORTED`). `Unknown` and `UNVERIFIED` are near-synonyms. This is two
independent lineages converging on nearly the same closed vocabulary — real evidence the
convergence is not arbitrary, closer to what a genuinely shared protocol term would look like
than a coincidence.

## What `ce-standing/1` conformance actually requires

1. A closed (not open-ended, not free-text) enum of evidence states, with each state's meaning
   defined precisely enough that two independent parties assign the same state to the same
   evidence.
2. No state inherits from a neighboring claim — `castle`'s own discipline (seen in
   `docs/jira/v26.8.18/00-OVERVIEW.md`: "No layer inherits `ALIVE` from a neighboring layer")
   generalizes directly into this fragment's conformance requirement.
3. `Refused`/`REFUSED` must be a real, reachable state — not merely theoretical — since a
   vocabulary where nothing can ever be refused is not doing real classification work.

## Real, scoped gap

**Update (2026-08-19): the reconciliation step named below is now done, in code and in doc, not
just as a proposal.** `docs/jira/v26.8.19/CE-STANDING-RECONCILED.md` is a new, real
term-by-term reconciliation table built from both real sources (castle's `ReleaseStanding` enum
at `~/castle/src/v26_8_18/topology.rs:38-46`, and this session's
`no-overclaiming-rust.md` vocabulary). The honest reconciliation needed **8** terms, not 7:
`UNVERIFIED, ALIVE, PARTIAL, BLOCKED, BUILD_BROKEN, MOCKED, UNSUPPORTED, REFUSED` —
`BUILD_BROKEN` has no session-vocabulary equivalent and `MOCKED` has no castle equivalent; both
are kept as first-class, non-collapsed terms, preserving the divergence this fragment's earlier
draft already flagged rather than papering over it.

This vocabulary is now also a real TypeScript artifact, not only prose:
`platform-console/app/lib/ce-standing.ts` exports the closed 8-member `CeStanding` union type, a
`CE_STANDING_DEFINITIONS` record (precise per-term definition plus each term's castle-equivalent
or `null`), a `CE_STANDING_VALUES` array, and an `isCeStanding` type guard. `npx tsc --noEmit`
from `platform-console/app` is clean against it.

What remains open: castle's Rust enum itself was left completely unchanged (correctly — it is
one of the two source vocabularies being reconciled, not the reconciliation's target) so the two
lineages still exist as two separate artifacts (a Rust enum, a TypeScript union) rather than one
shared cross-language definition any implementation could import directly; a genuinely shared
protocol vocabulary would need either a single source of truth both languages consume or a
generator, neither of which exists yet. No external party has reviewed or ratified
`CE-STANDING-RECONCILED.md` or `ce-standing.ts`.

## Explicit non-claims

- The two vocabularies have not been reconciled into a single ratified list in this pass.
- `BuildBroken` and `MOCKED` are named above as a genuine divergence, not swept into false
  equivalence.
- No external party has reviewed or ratified this fragment.
