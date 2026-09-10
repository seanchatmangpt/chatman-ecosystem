# Appendix C — ggen Pack Anatomy

A post-AGI ggen pack should be treated as an executable knowledge bundle, not merely a directory of templates.

## Recommended semantic contents

```text
pack/
├── ontology/          # public imports + custom domain terms
├── queries/           # bounded graph selections
├── templates/         # deterministic projections
├── shapes/            # SHACL or equivalent semantic constraints
├── proofs/            # formal obligations or theorem interfaces
├── validators/        # positive + negative verification packs
├── gyms/              # synthetic world/benchmark projections
├── interfaces/        # CLI/API/MCP/A2A projection metadata
├── receipts/          # receipt expectations and schemas
├── examples/          # admitted example instances
└── pack.toml          # identity, version, class, dependencies
```

The exact paths are illustrative; repository-owned schemas outrank this appendix.

## Pack contract

A pack should declare:

- class identity and applicability conditions;
- imported public ontology;
- custom ontology;
- deterministic inputs;
- generated projections;
- refusal modes;
- evidence gates;
- authority assumptions;
- replay requirements;
- version and dependency identities.

## Generated status

Generated artifacts should be replaceable from the pack's semantic source. If consumers must hand-edit a generated projection to make the class useful, the pack has not fully closed the class.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix C — ggen Pack Anatomy** is not retained as a label-only reference. This page is part of the semantic manufacturing pipeline. The durable asset is the knowledge needed to regenerate an artifact: ontology, query, constraints, template, dependency identity, admission rules, and verification procedure. Generated files are projections. Treating a projection as the canonical editing surface creates drift because the next generation pass can erase an apparently valid manual repair.

## System contract

A lawful manufacturing path is `graph -> query -> deterministic transform -> candidate artifact -> structural admission -> runtime verification -> receipt`. Every stage should have an explicit input identity and a falsifier. Manifests bind dependency closure; templates make construction repeatable; validators reject malformed candidates; tests challenge behavior; receipts bind what actually executed. None of these alone is proof of production behavior, but together they prevent the generator from self-attesting.

## Failure modes and falsifiers

The strongest maintenance test is regeneration from a clean checkout. If the same admitted inputs do not reproduce the same semantic artifact, if a required dependency is ambient rather than declared, or if a generated file must be manually patched to pass, the manufacturing system is not closed. The repair belongs upstream in the graph/query/template/validator, followed by regeneration and exact-head verification.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
