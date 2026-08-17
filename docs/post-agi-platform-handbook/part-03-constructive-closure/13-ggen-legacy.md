# 13. ggen-legacy and Reconstitution

The hardest systems to manufacture semantically are the ones that already exist.

They contain years of implicit decisions spread across source code, configuration, tests, CI, runtime behavior, documentation, tickets, naming conventions, and operator memory.

`ggen-legacy` addresses that epistemic boundary: recover enough meaning from a legacy artifact that the artifact can become a projection rather than the only surviving source of knowledge.

## Reconstitution is stronger than migration

A migration can copy an implementation from one substrate to another.

Reconstitution asks a more demanding question:

> Can we destroy the current projection and manufacture an equivalent admitted system again from recovered semantic sources and construction law?

The flow is:

\[
Legacy \rightarrow Observe \rightarrow Recover\ Ontology \rightarrow Recover\ Law \rightarrow Generate \rightarrow Verify
\]

## The epistemic fence

A legacy codebase is evidence, not automatically the intended specification.

Bugs, dead code, obsolete workarounds, abandoned features, and accidental behavior all coexist with essential invariants. The reconstitution process must therefore preserve before it normalizes.

Chesterton's Fence and execution evidence are essential. A strange branch may encode a production incident no document remembers.

## Recover public and custom ontology

Reconstitution should prefer public ontology for known concepts and define custom terms only where the legacy system expresses genuine domain meaning that public vocabularies do not capture.

This prevents the reverse-engineered ontology from becoming a one-to-one transcription of implementation trivia.

The goal is semantic compression, not RDF-shaped source code.

## Recover construction law

An ontology that says what objects exist is insufficient. The system must also recover how lawful artifacts are manufactured, admitted, validated, and actuated.

Tests, CI workflows, deployment scripts, schemas, and runtime traces are evidence about that law.

Where evidence conflicts, the conflict remains explicit until resolved.

## Reconstitution as a portfolio strategy

A large repository portfolio often contains POCs that were abandoned because the available models, infrastructure, or human time could not finish them.

Post-AGI reconstitution turns that latent reservoir into discoverable capability. Each repository can be surveyed, classified, lifted into ontology, and either closed, superseded, or manufactured into a current projection.

The objective is not to keep every repository alive. It is to preserve the knowledge and decide its standing explicitly.

## Falsifier

A “reconstituted” project fails if its generated version can only be maintained by continuing to hand-edit implementation-specific files that were supposed to be projections.

## Operational exercise

Select one legacy repository. Write three lists: observed behavior, inferred intent, and unknown intent. Recover the public ontology first, then add custom semantics. Only after admission should ggen manufacture the replacement projection.