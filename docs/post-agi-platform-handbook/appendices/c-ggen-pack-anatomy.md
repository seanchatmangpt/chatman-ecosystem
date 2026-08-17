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