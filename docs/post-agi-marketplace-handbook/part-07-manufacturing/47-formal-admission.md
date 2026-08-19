# 47. Formal Admission

## Generation is not correctness

Deterministic generation proves repeatability. Schema validation proves shape. Compilation proves type-level consistency. None alone proves the commercial invariants that protect customer rights and money.

Formal admission adds machine-checkable obligations where the domain is tractable.

## High-value invariants

Marketplace state machines are rich in safety properties:

```text
No fulfillment without active admitted entitlement.
No duplicate application of one entitlement event.
No stale event resurrects a newer canceled/revoked right.
No meter batch contains the same usage event twice.
No accepted meter batch is silently rewritten.
No agreement is billed by two active routes for the same right/window.
No external DO occurs without exact authority and receipt.
```

These can be encoded across SHACL, type systems, property tests, model checking, Lean, or other formal methods depending on cost and value.

## Structural proofs

SHACL or schema-level constraints can prove graph properties before code generation: cardinality, required mapping, units, effective intervals, source identities, and forbidden combinations.

A malformed `Entitlement` should fail before a vendor adapter is rendered.

## State-machine properties

Property tests and model checking can explore event permutations much more cheaply than hand-authored examples. Generate traces with duplicate, delayed, and contradictory lifecycle events and assert convergence or typed ambiguity.

One key property:

```text
∀ event.
  stale(event) ∧ terminal_newer_state(E)
  ⇒ apply(E, event) cannot reactivate rights
```

## Formal model correspondence

A theorem over a simplified state machine is useful only if production code can be shown to correspond to the formal model. The receipt should bind model version, generated/runtime source identity, and test/proof artifact.

`ggen renders; formal admission constrains; runtime qualification proves the implemented boundary.`

## Liveness as well as safety

A system that never activates anyone is safe from unauthorized activation but commercially useless. Formal work should also examine bounded liveness: valid accepted agreements eventually reach entitlement processing unless an explicit BLOCKED condition persists.

## Negative fixtures remain permanent

Every discovered counterexample becomes a regression fixture or theorem obligation. Fix the failed transition, not the test.

## Refusals

- `REFUSED:SYNTAX_VALIDATION_AS_SEMANTIC_PROOF`
- `REFUSED:SIMPLIFIED_MODEL_WITHOUT_IMPLEMENTATION_CORRESPONDENCE`
- `REFUSED:VACUOUS_SAFETY`
- `REFUSED:NEGATIVE_FIXTURE_WEAKENED`
- `REFUSED:PROOF_FROM_DIFFERENT_SOURCE_IDENTITY`

## Operational exercise

Formalize the stale-event entitlement property and the no-double-billing invariant. Produce one counterexample trace for each naive implementation. Then bind the fixed runtime transition or generated adapter to the model through executable correspondence tests.
