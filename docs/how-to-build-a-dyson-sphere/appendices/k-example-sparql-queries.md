# Appendix K — Example SPARQL Queries

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

The subject is treated as a bounded object in the larger stellar-manufacturing graph. Its inputs, outputs, constraints, failure modes, and evidence obligations must be explicit before the system may generalize from a local success to a reusable class.

## Sections

- [Find Available Material](k-01-find-available-material.md)
- [Find Safe Orbital Regions](k-02-find-safe-orbital-regions.md)
- [Find Unreceipted Actions](k-03-find-unreceipted-actions.md)
- [Find Unproven Collector Designs](k-04-find-unproven-collector-designs.md)
- [Find Resource Bottlenecks](k-05-find-resource-bottlenecks.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix K — Example SPARQL Queries** is not retained as a label-only reference. This page is part of the semantic manufacturing pipeline. The durable asset is the knowledge needed to regenerate an artifact: ontology, query, constraints, template, dependency identity, admission rules, and verification procedure. Generated files are projections. Treating a projection as the canonical editing surface creates drift because the next generation pass can erase an apparently valid manual repair.

## System contract

A lawful manufacturing path is `graph -> query -> deterministic transform -> candidate artifact -> structural admission -> runtime verification -> receipt`. Every stage should have an explicit input identity and a falsifier. Manifests bind dependency closure; templates make construction repeatable; validators reject malformed candidates; tests challenge behavior; receipts bind what actually executed. None of these alone is proof of production behavior, but together they prevent the generator from self-attesting.

## Failure modes and falsifiers

The strongest maintenance test is regeneration from a clean checkout. If the same admitted inputs do not reproduce the same semantic artifact, if a required dependency is ambient rather than declared, or if a generated file must be manually patched to pass, the manufacturing system is not closed. The repair belongs upstream in the graph/query/template/validator, followed by regeneration and exact-head verification.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
