# RFC v26.9.26 implementation seed — Executable Enterprise Architecture

Base: `main@c8dd167a94bf829c9011b7a6836feca6c180ff15`

## Canonical ownership

This repository owns the cross-repository laws for:

`Strategy -> OperatingModel -> Capability -> Requirement -> ABB -> ArchitectureContract -> CandidateSBB -> Qualification -> Selection/Manufacture -> Runtime -> Receipt`.

It also owns the semantic separation laws:

- ABB != SBB != Pack != artifact.
- Capability != authority != DO != standing.
- Qualification MUST bind an immutable exact subject.
- UNKNOWN MUST remain first-class.
- Reuse -> compose -> extend -> invent.
- BRCE remains the consequential authority boundary; SBB qualification cannot widen authority.
- Industry Closure means selection + specialization + manufacture over an admitted enterprise-architecture design space, not one canonical vendor stack.

## Seed delivered

- `ontology/enterprise-architecture-v26.9.26.ttl`: canonical EA vocabulary.
- `ontology/enterprise-architecture-v26.9.26.shacl.ttl`: initial exact-subject/qualification shapes.

## Definition of done for follow-on agents

1. Add executable tests proving ABB/SBB/Pack type separation.
2. Add deterministic qualification receipt schema with subject, contract, evidence and digest binding.
3. Add fail-closed typed refusals for mutable subject, missing evidence, authority widening and UNKNOWN promotion.
4. Add DfCM candidate-frontier query/validation for at least two SBB candidates behind one ABB.
5. Add Industry Closure vocabulary for strategy patterns, operating models, capability/value-stream maps, ABB catalogs, transition patterns and governance.
6. Add canonical cross-repo projection manifest consumed by ggen-marketplace, ggen, ash_kudzu, ash_atlassian, ash_a2a, xaas, autofde-lab, gymact and affidavit.
7. Add an end-to-end executable witness:
   Strategy -> Capability -> ABB -> Contract -> CandidateSBBs -> QualifiedSBB -> manufacture/runtime candidate -> receipt.
8. Prove qualification never creates BRCE authority.

Do not close this RFC with prose-only artifacts. Standing requires executable semantic courts against exact subjects.
