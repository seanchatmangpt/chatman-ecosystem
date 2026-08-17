# 42. Source Code as a Projection

Software engineering traditionally treats source code as the privileged description of a system. In the post-AGI limit, that privilege weakens.

Source remains important because compilers and runtimes consume it. But when the durable semantics live in ontology, constraints, process models, and manufacturing law, source code becomes one executable projection among several.

## Programs from ontology

A semantic model can define entities, relationships, invariants, capabilities, messages, policies, processes, and evidence obligations. ggen can project those semantics into language-specific types and implementations.

\[
G^* \xrightarrow{ggen_{Rust}} Source_{Rust}
\]

\[
G^* \xrightarrow{ggen_{TypeScript}} Source_{TS}
\]

The languages differ. The semantic capability should not.

## Schemas, types, and protocols

JSON Schema, protobuf, OpenAPI, GraphQL, database DDL, Rust types, TypeScript types, and validation code often restate the same domain distinctions.

Post-AGI manufacture should derive as many of these as possible from a shared source, with semantic CI verifying correspondence.

## Tests can also be projections

Positive and negative fixtures can be generated from semantic constraints. This does not eliminate manually discovered regression tests. Those tests are new evidence and may reveal missing ontology or construction law.

The useful direction is recursive:

\[
Discovery \rightarrow Test \rightarrow Semantic\ Gap \rightarrow Ontology' \rightarrow Generated\ Tests'
\]

## Handwritten code becomes high-information code

When boilerplate is manufactured, manually authored code should increasingly represent genuinely novel algorithms, substrate-specific adapters, irreducible domain behavior, or temporary exploration.

The objective is not “zero source code.” It is zero unnecessary independent semantic authority inside source code.

## Programming languages become targets

Language choice can then be selected by constraints such as runtime, ecosystem, safety, latency, verification, deployment size, or interoperability rather than by the assumption that the language itself owns the domain model.

## Falsifier

Source is not yet a projection if deleting it destroys domain meaning that cannot be reconstructed from admitted semantic sources or deliberately classified handwritten logic.

## Operational exercise

Take one service and classify every source file as generated projection, substrate adapter, novel domain logic, test evidence, or unexplained manual semantics. The final category is the target for reconstitution.