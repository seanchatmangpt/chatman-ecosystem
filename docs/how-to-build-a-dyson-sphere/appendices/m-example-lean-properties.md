# Appendix M — Example Lean Properties

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

Formal admission is used only where a machine-checkable invariant can be stated precisely. The critical separation is that rendering, proving, and certifying are different operations: ggen can render a candidate, Lean can discharge a theorem obligation, and mfact can bind evidence to a subject. None of those steps grants DO authority by itself.

## Sections

- [Orbital Safety](m-01-orbital-safety.md)
- [Mass Conservation](m-02-mass-conservation.md)
- [Energy Bounds](m-03-energy-bounds.md)
- [Authority Non-Escalation](m-04-authority-non-escalation.md)
- [Receipt Completeness](m-05-receipt-completeness.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix M — Example Lean Properties** is not retained as a label-only reference. This page defines semantic interoperability, not vocabulary for its own sake. The ontology layer gives independently implemented systems a common meaning for objects, relations, quantities, constraints, authority, and evidence. That meaning must survive transport across RDF stores, generators, simulators, formal checkers, telemetry pipelines, and runtime adapters without a repository-specific interpretation becoming the hidden source of truth.

## System contract

The operational contract is `public meaning -> local extension -> SHACL/admission -> generated projection`. Classes identify what a thing is; properties state relations or measurements; QUDT-style units prevent dimension confusion; SHACL shapes turn semantic assumptions into executable constraints; mappings preserve correspondence to external standards. An extension is lawful only when it narrows or composes public semantics rather than redefining them incompatibly.

## Failure modes and falsifiers

A useful ontology page names its failure modes. Two systems using the same label with different units, a class whose identity cannot be reconciled, a property whose domain/range is ambiguous, or a shape that accepts an invalid state are semantic defects. The falsifier is a concrete graph that should be rejected but passes, or a valid graph that cannot round-trip through the declared mapping. Those examples belong in tests because semantic drift is otherwise invisible until actuation.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
