# Appendix E.3 — Queries

**Parent:** [Appendix E — ggen Pack Layout](e-ggen-pack-layout.md)

ggen is treated as a semantic manufacturing compiler: graph and query select meaning, templates render projections, validators reject malformed output, and receipts bind the generated artifact to the admitted subject. Generation is not evidence of correctness. The value of the generator is reproducibility and class closure—once a construction pattern is admitted, it can be regenerated for new subjects without rediscovering the pattern manually.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix E.3 — Queries** is not retained as a label-only reference. This page is part of the semantic manufacturing pipeline. The durable asset is the knowledge needed to regenerate an artifact: ontology, query, constraints, template, dependency identity, admission rules, and verification procedure. Generated files are projections. Treating a projection as the canonical editing surface creates drift because the next generation pass can erase an apparently valid manual repair.

## System contract

A lawful manufacturing path is `graph -> query -> deterministic transform -> candidate artifact -> structural admission -> runtime verification -> receipt`. Every stage should have an explicit input identity and a falsifier. Manifests bind dependency closure; templates make construction repeatable; validators reject malformed candidates; tests challenge behavior; receipts bind what actually executed. None of these alone is proof of production behavior, but together they prevent the generator from self-attesting.

## Failure modes and falsifiers

The strongest maintenance test is regeneration from a clean checkout. If the same admitted inputs do not reproduce the same semantic artifact, if a required dependency is ambient rather than declared, or if a generated file must be manually patched to pass, the manufacturing system is not closed. The repair belongs upstream in the graph/query/template/validator, followed by regeneration and exact-head verification.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
