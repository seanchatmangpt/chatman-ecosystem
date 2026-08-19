# ce-capability/1 — SELECT / CONSTRUCT / DO as a Closed, Ordered Algebra

> Status: draft, fragment of the `ce-*` protocol family. The algebra
> [`08-CE-CONSEQUENCE-1.md`](08-CE-CONSEQUENCE-1.md) and [`07-CE-AUTHORITY-1.md`](07-CE-AUTHORITY-1.md)
> both presuppose.

## The claim this fragment formalizes

`SELECT` (retrieval/observation), `CONSTRUCT` (manufacture), and `DO` (consequential actuation)
form a closed algebra where no operation silently upgrades into a more powerful one — a `SELECT`
can never become a `DO` by accident, and a `CONSTRUCT` can never become a `DO` without passing
through the `ce-authority/1`/`ce-consequence/1` chokepoint.

## Checked against real code — this is the most independently-evidenced fragment of the seven

Three separate, real codebases already enforce a version of this boundary, checked directly
rather than assumed from naming conventions:

1. **`castle`**: `~/castle/src/fortune5_generated.rs`'s `F5-AUTH-002`/`F5-AIRGAP-001/002`
   (see `08-CE-CONSEQUENCE-1.md`) — `CONSTRUCT` has zero actuation authority and zero
   network/secret dependencies, checked as formal, generated Fortune-5 controls.
2. **`platform-console`**: `app/lib/castle.ts`'s own header comment (quoted verbatim in this
   session's earlier turns) states there is "no code path anywhere in this file that could
   construct a `castle construct` or `castle gymact` invocation even if such a verb existed in a
   future castle release" — the boundary is enforced by the *absence* of a code path, not by a
   runtime check that could be bypassed.
3. **`ggen`**: `pack-lifecycle.md`'s documented policy (checked this session via the
   `ggen-marketplace` speedrun): "Verify consequence — the consumer's native tests, compilers,
   or external oracles establish whether the manufactured artifact has the required behavior" —
   `ggen`'s own `CONSTRUCT` step (pack generation) explicitly disclaims that it proves anything
   about the target's real behavior; that proof requires a separate, external `DO`-adjacent step
   (the consumer's own compiler/test run).

## What `ce-capability/1` conformance actually requires

1. `SELECT`, `CONSTRUCT`, `DO` are the only three operation classes — an implementation adding a
   fourth class must show it reduces to one of these three, not silently create a bypass.
2. No implementation detail allows `SELECT` or `CONSTRUCT` output to be treated as already-
   admitted for `DO` purposes — every transition to `DO` passes through `ce-authority/1`'s
   external object.
3. The absence-of-code-path pattern (`platform-console/app/lib/castle.ts`'s real example) is a
   *stronger* conformance signal than a runtime flag check, because it cannot be misconfigured
   at deploy time — implementations should prefer it where feasible.

## Real, scoped gap

The three real examples above are each independently enforced in their own codebase's own
idiom (a generated Fortune-5 control in Rust, an absent-code-path argument in TypeScript, a
documented policy disclaimer in `ggen`'s markdown) — there is no single, shared, checkable test
suite that verifies all three simultaneously against the same formal definition of `SELECT`/
`CONSTRUCT`/`DO`. Building that shared conformance suite is `ce-capability/1`'s concrete
buildable-now item, and it is the natural site for `ce-standing/1`'s vocabulary to report each
implementation's result in.

## Explicit non-claims

- Each of the three codebases' enforcement is real and independently checked; no shared,
  cross-codebase conformance suite exists yet.
- No external party has reviewed or ratified this fragment.
