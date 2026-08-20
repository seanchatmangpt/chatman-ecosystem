# Appendix G — GymAct World Specification

A minimal world specification should define:

1. ontology and object classes;
2. initial state generator;
3. observation function;
4. available action classes;
5. action preconditions;
6. transition function;
7. refusal/failure states;
8. resource and cost model;
9. termination conditions;
10. evidence emitted by each transition;
11. correspondence assumptions linking the gym to the claimed real-world class.

## Two observation modes

A strong benchmark often provides both:

- **full modeled state**, for upper-bound planning experiments; and
- **bounded observation**, for realistic AutoFDE/agent evaluation.

Do not mix the scores without naming the information regime.

## Safety rule

Gym execution is CONSTRUCT/experimental execution. Promotion to real DO always requires independent operational admission.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix G — GymAct World Specification** is not retained as a label-only reference. This page belongs to the observation boundary: it explains how a real subject becomes an admitted, replayable description rather than an unqualified bag of facts. Observation is always partial. The carrier must bind exact subject identity, measurement time, source provenance, units, uncertainty, contradiction state, and the dimensions that remain UNKNOWN. A digest identifies the carrier; it does not make the carrier true.

## System contract

The operational sequence is `raw signal -> normalization -> provenance -> contradiction handling -> O* admission`. A value can be syntactically present yet inadmissible because its source is stale, its units are unresolved, or another source contradicts it. The critical rule is that UNKNOWN is preserved as topology. Missing knowledge may remove candidate actions from the lawful frontier, but it cannot be converted into permission merely because a planner prefers progress.

## Failure modes and falsifiers

Falsifiers are identity drift, stale observations reused against a changed subject, loss of provenance, contradictory measurements collapsed without a rule, and a regenerated observation whose digest cannot be reproduced from the same admitted inputs. Any of these lowers standing. The recovery path is re-observation and re-admission, not manual assertion that the old world model is still close enough.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
