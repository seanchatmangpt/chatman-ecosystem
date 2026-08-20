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

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix I — Lean Admission Patterns** is not retained as a label-only reference. This page sits on the irreversible boundary between choosing a possibility and changing the world. SELECT, CONSTRUCT, and DO are separate authorities. Search may explore many reversible candidates; construction may manufacture an artifact or counterfactual; only an explicitly admitted grant for the exact subject and consequence class can authorize DO. Access to a connector, credential, model, or command runner is capability—not authority.

## System contract

The brokered sequence is `intent -> exact-subject admission -> authority check -> consequence bound -> receipt reservation -> actuator -> observation -> reconciliation -> final receipt`. Relevant UNKNOWN refuses before DO. Ambiguous actuation does not turn into a retry loop. Replay verifies prior evidence and intentionally lacks an actuator edge. These separations keep autonomous operation from becoming ambient permission.

## Failure modes and falsifiers

Permanent falsifiers include accepting a nearby authority class, allowing a grant for one subject to mutate another, invoking an actuator before reservation is durable, promoting transport ACK to DONE, or letting a planner/model/hook manufacture its own authority. Any such edge is a constitutional defect even if the resulting state happens to be desirable.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
