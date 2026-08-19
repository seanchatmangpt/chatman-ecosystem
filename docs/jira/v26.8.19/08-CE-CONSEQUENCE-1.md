# ce-consequence/1 — DO Exists Only When Authority Admits That Exact Consequence

> Status: draft, fragment of the `ce-*` protocol family. Composes with
> [`07-CE-AUTHORITY-1.md`](07-CE-AUTHORITY-1.md) (the object doing the admitting) and
> [`06-CE-RECEIPT-1.md`](06-CE-RECEIPT-1.md) (the precondition on the actuation this fragment
> gates).

## The claim this fragment formalizes

> `SELECT(x)` does not gain authority because a planner produced it. `CONSTRUCT(x)` does not
> gain authority because ggen manufactured it. `DO(x)` exists only when an external authority
> object admits that exact consequence.

This is the sharpest, most checkable part of the whole inversion, because `castle`'s own real
Fortune-5 requirement set already states a version of it as a formal control.

## Checked against real code — this fragment is unusually well-evidenced already

`~/castle/src/fortune5_generated.rs:16`:

```
Fortune5Requirement { order: 210, control_id: "F5-AUTH-002", category: "authority",
  description: "CONSTRUCT has no consequential actuation authority.",
  metric: "construct_actuation_authority", comparator: "EQ", target: "false",
  authority: "REQUIRED" }
```

This is not a proposal — it is a real, already-shipped, checkable control in `castle`'s
generated requirement set, with a real metric name (`construct_actuation_authority`) that a real
conformance run presumably evaluates to `false`. `fortune5_generated.rs:43-44` extends the same
discipline to a stronger claim: the `CONSTRUCT` capsule has *zero network dependencies* and
*zero secret dependencies* (`F5-AIRGAP-001`, `F5-AIRGAP-002`) — meaning `CONSTRUCT` in `castle`'s
model is not merely authority-less, it is architecturally incapable of reaching outside its own
capsule to attempt an actuation, which is a stronger and more verifiable property than a runtime
check that could in principle be bypassed.

`~/castle/src/castle.rs`'s own module header independently names "the exclusive [DO path]" —
language consistent with `DO` being a single, gated chokepoint rather than one of several ways
to cause a consequence.

## What `ce-consequence/1` conformance actually requires

1. `SELECT` and `CONSTRUCT` outputs, however produced, carry no actuation capability of their
   own — checked structurally (no network/secret access from the CONSTRUCT capsule, per
   `F5-AIRGAP-001/002`'s stronger standard), not merely by a runtime flag that could be
   misconfigured.
2. `DO(x)` requires a distinct call into an `Authority` object (per `ce-authority/1`) that
   evaluates the *exact* consequence `x`, not a class of consequences `x` belongs to — a
   capability being generally admitted does not mean every specific instance of it is.
3. A `SELECT`/`CONSTRUCT` result that is never submitted to `Authority` for a `DO` decision
   remains permanently inert — there is no code path by which planning or manufacturing alone
   causes a real-world effect.

## Real, scoped gap

`castle`'s own metric (`construct_actuation_authority == false`) is evidenced as a control
*definition*, not as a live-run conformance result in this pass — whether the metric currently
evaluates to `false` on the live codebase was not re-verified here (it would require running
`castle`'s own conformance suite, not reading its source). `platform-console`'s side of this
fragment is weaker than `castle`'s: `app/lib/castle.ts`'s `resolveCastleVerb` (see
`ce-authority/1`) shows capability admission still coupled to a static table rather than a
separate per-instance `Authority` evaluation — meaning `ce-consequence/1`'s requirement 2 (exact-
consequence evaluation, not class-membership evaluation) is not yet met on the
`platform-console` side even where `ce-authority/1`'s narrower requirement (an external object
exists at all) partially is.

## Explicit non-claims

- `castle`'s `F5-AUTH-002`/`F5-AIRGAP-001/002` controls are real and shipped as definitions;
  their current pass/fail state on a live conformance run was not re-checked in this pass.
- `platform-console` does not conform to requirement 2 above.
- No external party has reviewed or ratified this fragment.
