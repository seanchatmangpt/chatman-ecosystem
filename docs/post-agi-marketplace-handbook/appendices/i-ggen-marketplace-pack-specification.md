# Appendix I — ggen Marketplace Pack Specification

A marketplace pack is a dependency-closed unit of executable integration knowledge.

## Directory shape

```text
pack/
  pack.toml
  ontology/
    marketplace.ttl
    shapes.ttl
  queries/
  templates/
  schemas/
  fixtures/
    positive/
    negative/
  qualification/
  docs/
  receipts/
```

## `pack.toml`

The manifest should bind:

```text
pack_id
pack_version
marketplace
vendor_contract_observed_at
canonical_ontology_digest
public_ontology_imports
custom_namespace
ggen_version
generator_inputs
outputs
required_gates
known_exclusions
required_authority_classes
```

## Fixtures

Positive fixtures demonstrate supported lifecycle traces. Negative fixtures prove refusals for stale events, bad signatures, unmapped products, illegal transitions, duplicate financial intents, and unsupported capabilities.

Never delete a negative fixture merely to obtain a green qualification.

## Output classes

A pack may generate:

- listing metadata;
- vendor API models;
- entitlement adapters;
- meter clients;
- deployment packages;
- identity mapping schemas;
- qualification suites;
- documentation;
- receipt schemas;
- marketplace capability descriptors.

Generated output is a projection and should carry a header or manifest pointer back to its canonical source and pack version.

## Qualification

```text
source correspondence
→ ontology/SHACL
→ deterministic generation
→ schema/compile
→ positive fixtures
→ negative fixtures
→ contract tests
→ gym episodes
→ sandbox/live qualification
```

Marketplace pack publication standing is independent from the standing of a product generated with the pack.
