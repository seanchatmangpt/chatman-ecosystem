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

The two vocabularies above have never been formally reconciled into one shared, versioned term
list — they independently converged, which is evidence *for* the fragment's plausibility, but
convergence-by-accident is not the same as a ratified shared spec. `ce-standing/1`'s real next
step is a literal side-by-side reconciliation table (`castle`'s seven terms against this
session's seven terms) producing one canonical `ce-standing/1` vocabulary, plus a note on where
the two lineages genuinely diverge (`BuildBroken` vs. `MOCKED` do not mean quite the same thing
— `BuildBroken` names a compile/runtime failure, `MOCKED` names a test-double substitution;
collapsing them would lose real distinguishing information).

## Explicit non-claims

- The two vocabularies have not been reconciled into a single ratified list in this pass.
- `BuildBroken` and `MOCKED` are named above as a genuine divergence, not swept into false
  equivalence.
- No external party has reviewed or ratified this fragment.
