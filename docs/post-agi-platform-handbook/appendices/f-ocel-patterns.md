# Appendix F — OCEL 2.0 Process-State Patterns

## Release pattern

Objects:

- repository;
- commit;
- pull request;
- build artifact;
- release;
- receipt.

Events:

- observe source;
- admit candidate;
- validate;
- publish branch;
- open draft PR;
- exact-head verify;
- release;
- supersede.

## Deployment pattern

Objects:

- release artifact;
- environment;
- workload;
- policy;
- authority grant;
- receipt.

Events:

- construct deployment;
- admit DO;
- actuate;
- observe postcondition;
- verify standing;
- rollback or supersede.

## Process-state rule

Prefer deriving current state from admitted object-event relationships rather than maintaining an unrelated status field as a second semantic authority.

Caches and projections are allowed when their derivation is explicit.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix F — OCEL 2.0 Process-State Patterns** is not retained as a label-only reference. OCEL-style process evidence models events around multiple participating objects instead of forcing reality into one case identifier. That matters for fleets where one actuation can touch a subject, authority grant, artifact, organization, receipt, and external resource simultaneously. Event identity, object identity, timestamps, activity type, and object relationships must therefore remain first-class and replayable.

## System contract

The event log is observation, not authority. It can reconstruct causality, measure throughput and waiting, detect conformance violations, and feed process mining, but it cannot retroactively authorize an action. Derived process models must preserve provenance back to events and state which projection or aggregation produced the view. Otherwise a convenient dashboard can silently become a second source of truth.

## Failure modes and falsifiers

Falsifiers include orphan events, reused object identities, impossible temporal ordering, missing authority/receipt objects for consequential events, or a replay whose derived process state differs from the original under the same event set. These should be executable integrity checks on the OCEL export/import boundary.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
