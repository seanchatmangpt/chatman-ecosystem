# Appendix L — Example SHACL Shapes

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities.

## Sections

- [Collector Shape](l-01-collector-shape.md)
- [Orbit Shape](l-02-orbit-shape.md)
- [Factory Shape](l-03-factory-shape.md)
- [Authority Shape](l-04-authority-shape.md)
- [Receipt Shape](l-05-receipt-shape.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix L — Example SHACL Shapes** is not retained as a label-only reference. This page defines semantic interoperability, not vocabulary for its own sake. The ontology layer gives independently implemented systems a common meaning for objects, relations, quantities, constraints, authority, and evidence. That meaning must survive transport across RDF stores, generators, simulators, formal checkers, telemetry pipelines, and runtime adapters without a repository-specific interpretation becoming the hidden source of truth.

## System contract

The operational contract is `public meaning -> local extension -> SHACL/admission -> generated projection`. Classes identify what a thing is; properties state relations or measurements; QUDT-style units prevent dimension confusion; SHACL shapes turn semantic assumptions into executable constraints; mappings preserve correspondence to external standards. An extension is lawful only when it narrows or composes public semantics rather than redefining them incompatibly.

## Failure modes and falsifiers

A useful ontology page names its failure modes. Two systems using the same label with different units, a class whose identity cannot be reconciled, a property whose domain/range is ambiguous, or a shape that accepts an invalid state are semantic defects. The falsifier is a concrete graph that should be rejected but passes, or a valid graph that cannot round-trip through the declared mapping. Those examples belong in tests because semantic drift is otherwise invisible until actuation.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
