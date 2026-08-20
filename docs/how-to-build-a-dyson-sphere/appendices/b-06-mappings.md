# Appendix B.6 — Mappings

**Parent:** [Appendix B — Reference Ontology](b-reference-ontology.md)

The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix B.6 — Mappings** is not retained as a label-only reference. This page defines semantic interoperability, not vocabulary for its own sake. The ontology layer gives independently implemented systems a common meaning for objects, relations, quantities, constraints, authority, and evidence. That meaning must survive transport across RDF stores, generators, simulators, formal checkers, telemetry pipelines, and runtime adapters without a repository-specific interpretation becoming the hidden source of truth.

## System contract

The operational contract is `public meaning -> local extension -> SHACL/admission -> generated projection`. Classes identify what a thing is; properties state relations or measurements; QUDT-style units prevent dimension confusion; SHACL shapes turn semantic assumptions into executable constraints; mappings preserve correspondence to external standards. An extension is lawful only when it narrows or composes public semantics rather than redefining them incompatibly.

## Failure modes and falsifiers

A useful ontology page names its failure modes. Two systems using the same label with different units, a class whose identity cannot be reconciled, a property whose domain/range is ambiguous, or a shape that accepts an invalid state are semantic defects. The falsifier is a concrete graph that should be rejected but passes, or a valid graph that cannot round-trip through the declared mapping. Those examples belong in tests because semantic drift is otherwise invisible until actuation.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
