# Appendix I — Lean Admission Patterns

Lean is most useful when the proposition to be proved is explicit and the trusted kernel remains independent of the generator.

## Pattern: semantic invariant

Prove that a graph transformation preserves a required relationship under stated assumptions.

## Pattern: authority non-reachability

Model a bounded authority graph and prove that an untrusted class has no path to a prohibited transition under the encoded rules.

## Pattern: class transfer

Prove that a parameterized construction preserves invariants for every member satisfying the class predicate.

## Pattern: projection commutation

Prove, where the semantics are formalizable, that two generated projections preserve the same canonical operation.

## Boundary

A Lean theorem does not prove that the live cloud, filesystem, network, or physical environment matches the formal model. Correspondence remains an observation and evidence obligation.