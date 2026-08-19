# 43. Marketplace Pack Architecture

## A pack is executable knowledge

A marketplace pack is not a template folder. It is a dependency-closed representation of what is known about projecting a canonical commercial product into one marketplace class.

A strong pack contains:

```text
pack.toml
ontology/
constraints/
queries/
templates/
schemas/
fixtures/positive/
fixtures/negative/
qualification/
docs/
receipts/
```

## Manifest

`pack.toml` should bind marketplace identity, pack version, vendor contract observation date, ontology/source digests, imported public vocabularies, custom namespace, generator compatibility, outputs, qualification gates, authority classes, known gaps, and exclusions.

A pack whose vendor source date is unknown is already stale evidence.

## Ontology and constraints

The ontology maps vendor concepts to canonical classes and records extensions. Constraints prove the input graph is suitable for this projection.

Example:

```text
AWS:LicenseArn mapsTo MarketplaceLicenseIdentity
Alibaba:ServiceInstance mapsTo FulfillmentInstance (NARROWER/EXTENSION as proven)
Salesforce:SubscriberOrg mapsTo TenantIdentity
```

Do not put these mappings in prose only. The generator and qualification suite should consume the same semantic record.

## Fixtures are the pack's executable memory

Positive fixtures encode known-good lifecycle examples. Negative fixtures protect boundaries:

- invalid signature/issuer;
- unmapped product or plan;
- stale event;
- duplicate event;
- illegal state transition;
- unsupported pricing model;
- ambiguous metering response;
- unreceipted DO attempt;
- vendor enum/schema drift.

Never delete a negative fixture merely to obtain green CI.

## Qualification

A pack should define its ladder:

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

Not every marketplace exposes a sandbox. That becomes an explicit limitation in the qualification plan, not a reason to promote static evidence.

## Pack standing versus product standing

A pack can be ALIVE for generating/validating its declared projection while a particular product generated from it remains UNKNOWN. Conversely, a product might have manually qualified legacy integration while the new pack remains PARTIAL_ALIVE.

Keep the subjects separate.

## Distribution

`ggen-marketplace` is the natural distribution surface for reusable packs. The Chatman ecosystem composition root should reference pack identities and standing rather than copy every pack implementation into one repository.

## Operational exercise

Specify a complete pack manifest for one marketplace. Include upstream source observations, canonical mappings, output classes, negative fixtures, authority requirements, live gates, receipts, and the exact condition that would invalidate prior standing.
