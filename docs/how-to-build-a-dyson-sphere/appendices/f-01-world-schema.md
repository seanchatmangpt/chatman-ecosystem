# Appendix F.1 — World Schema

**Parent:** [Appendix F — gymact Environment](f-gymact-environment.md)

GymAct provides counterfactual execution before physical consequence. A world model names its state, roles, policies, observation projections, action projections, authority, and episode boundaries. Simulation can falsify a candidate or expose missing constraints, but it cannot prove the physical world will behave identically; its standing is experimental evidence, not deployment evidence.

## Minimal record

```text
subject = <exact identity>
observed = <bounded inputs>
admitted = <constraints and uncertainty>
authority = <SELECT|CONSTRUCT|DO>
executed = <observed action or NONE>
verified = <postcondition evidence>
receipt = <content identity>
replay = <deterministic reconstruction method>
standing = <bounded status>
```

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix F.1 — World Schema** is not retained as a label-only reference. This page belongs to the observation boundary: it explains how a real subject becomes an admitted, replayable description rather than an unqualified bag of facts. Observation is always partial. The carrier must bind exact subject identity, measurement time, source provenance, units, uncertainty, contradiction state, and the dimensions that remain UNKNOWN. A digest identifies the carrier; it does not make the carrier true.

## System contract

The operational sequence is `raw signal -> normalization -> provenance -> contradiction handling -> O* admission`. A value can be syntactically present yet inadmissible because its source is stale, its units are unresolved, or another source contradicts it. The critical rule is that UNKNOWN is preserved as topology. Missing knowledge may remove candidate actions from the lawful frontier, but it cannot be converted into permission merely because a planner prefers progress.

## Failure modes and falsifiers

Falsifiers are identity drift, stale observations reused against a changed subject, loss of provenance, contradictory measurements collapsed without a rule, and a regenerated observation whose digest cannot be reproduced from the same admitted inputs. Any of these lowers standing. The recovery path is re-observation and re-admission, not manual assertion that the old world model is still close enough.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
