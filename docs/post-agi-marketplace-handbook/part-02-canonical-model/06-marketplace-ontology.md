# 6. Marketplace Ontology

## Ontology before integration

Marketplace APIs provide wire contracts. They do not provide a neutral theory of commerce. Two vendors can use the word `subscription` for objects with different lifecycle, pricing, identity, or entitlement semantics. Marketplace ontology prevents names from becoming accidental equivalence proofs.

The method is public ontology first, custom remainder second.

Candidate public vocabularies include PROV-O for provenance, ORG for organizational structure, DCAT and DCTERMS for catalog/document concepts, SKOS for controlled concepts, ODRL for rights and policy, QUDT for units, and SHACL for constraints. They are reused only where their semantics fit.

```text
O_marketplace = O_public-admitted ∪ O_custom-proven
```

A vendor's `offerId`, `LicenseArn`, package identifier, certification state, or private-offer status remains vendor-specific unless an exact mapping has been established.

## Objects and morphisms

The ontology should distinguish at least:

- product and product version;
- capability and commercial plan;
- proposed offer and accepted agreement;
- agreement and effective entitlement;
- entitlement and fulfillment;
- raw usage event and aggregated meter batch;
- billed amount and settled payout;
- organization, marketplace account, tenant, and human principal;
- artifact identity and product identity;
- receipt and authority.

The morphisms are equally important. `derivesFrom`, `projectsAs`, `authorizes`, `fulfilledBy`, `aggregates`, `reconciles`, and `evidences` are not interchangeable generic relationships.

## Refuse semantic debt early

A common integration shortcut is to define one giant `MarketplaceSubscription` interface and force every vendor into it. That seems elegant until one vendor supports contract quantity, another instantiated SaaS lifecycle, another package licensing, and another data-share access. The interface then accumulates optional fields whose absence has no typed meaning.

Ontology offers a better decomposition: represent the canonical semantic classes, then let each marketplace pack declare its mappings, extensions, and unsupported edges.

```text
VendorTerm
  → EQUIVALENT CanonicalTerm
  → NARROWER CanonicalTerm
  → BROADER CanonicalTerm
  → EXTENSION
  → UNKNOWN
```

`UNKNOWN` is a valid result. Unfamiliar does not mean invalid, but similarity does not prove equivalence.

## SHACL and admission

Structural constraints should run before generation. Examples:

```text
Plan must belong to exactly one canonical product family.
Entitlement must reference one agreement and an effective interval.
UsageDimension must declare a unit.
MarketplaceProjection must declare its marketplace and source observation date.
VendorMapping must declare a mapping kind.
```

The shapes are part of `O*` admission. A generator should never be asked to make malformed semantic input look plausible.

## Versioning

Marketplace ontology is versioned against both internal product semantics and external vendor observations. Vendor documentation changes can invalidate a mapping without changing application code. A qualification receipt should therefore bind the ontology digest and the marketplace contract observation date.

## Typed refusals

- `REFUSED:PUBLIC_EQUIVALENT_REDEFINED`
- `REFUSED:FALSE_VENDOR_EQUIVALENCE`
- `REFUSED:SHACL_ADMISSION_FAILURE`
- `REFUSED:UNBOUNDED_CUSTOM_TERM`
- `REFUSED:UNKNOWN_MAPPING_AS_EQUIVALENT`

## Operational exercise

Map `Product`, `Organization`, `Agreement`, `Entitlement`, `UsageEvent`, `Unit`, and `Receipt` to public ontology where defensible. Then map one AWS, Microsoft, Salesforce, and Alibaba vendor term. Preserve every unresolved mapping as `UNKNOWN` rather than inventing a shared meaning.
