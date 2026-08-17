# 15. SHACL, Constraints, and Typed Refusal

Construction abundance creates a filtering problem. A post-AGI system may be able to manufacture far more candidate graphs than should ever progress toward execution.

Constraint systems make exclusion mechanical.

## SHACL at the semantic boundary

SHACL is useful because it validates RDF graphs against explicit shapes. A capability can require properties, cardinalities, datatypes, class relationships, and conditional structures before a projection is admitted.

This moves failure earlier:

\[
Candidate\ Graph \rightarrow Validate \rightarrow Admit\ or\ Refuse
\]

rather than waiting for a generated artifact to fail deep inside a runtime.

## Constraints are layered

Not every invariant belongs in SHACL.

A practical hierarchy includes:

- semantic shape constraints;
- type-system constraints;
- theorem-level invariants;
- policy and authority constraints;
- runtime preconditions;
- empirical postconditions.

The important property is that each refusal identifies which layer rejected the transition.

## Typed refusal is behavior

A system that merely throws `error` discards topology.

Typed refusal preserves the reason a path is unavailable. This lets DfCM continue exploring lawful alternatives and allows future systems to learn which constraints commonly eliminate candidates.

`UNSUPPORTED` should not be conflated with `REFUSED`. Unsupported means the capability is not presently implemented or represented. Refused means a known transition was evaluated and found inadmissible under a declared rule.

Likewise `BLOCKED` is not necessarily failure. It can mean a required external dependency or authority is unavailable.

## Negative fixtures are constitutional assets

A negative test proves that an excluded state remains excluded. Such fixtures must not be weakened merely to obtain a green build.

In a post-AGI factory, negative behavior can be more important than positive generation because the generator will usually find *some* candidate. The safety property is often that it cannot cross a forbidden boundary.

## Refusal improves the graph

Each refusal can become reusable knowledge:

\[
(candidate, constraint, refusal) \rightarrow topology
\]

Over time, the system learns which regions of the construction space are impossible, expensive, unauthorized, or historically unstable.

## Falsifier

A system fails this chapter if invalid inputs are silently coerced into valid-looking outputs without preserving the violation or requesting explicit repair.

## Operational exercise

For one platform capability, write at least five negative fixtures: malformed identity, stale subject, unauthorized target, conflicting policy, and invalid semantic shape. Ensure the system produces distinguishable refusal evidence for each.