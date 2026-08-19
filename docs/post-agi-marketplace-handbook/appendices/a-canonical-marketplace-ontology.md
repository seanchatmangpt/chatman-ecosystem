# Appendix A — Canonical Marketplace Ontology

The canonical marketplace ontology exists to keep commercial meaning stable while implementation surfaces change.

## Core classes

```text
CommercialProduct
ProductVersion
Capability
Plan
Offer
Agreement
Entitlement
Fulfillment
UsageDimension
UsageEvent
MeterBatch
InvoiceReference
Settlement
SupportPolicy
SecurityClaim
DeploymentClass
MarketplaceProjection
Organization
MarketplaceAccount
Receipt
StandingClaim
```

## Identity rules

1. `CommercialProduct` identity is not a marketplace listing identifier.
2. `ProductVersion` identity is not a container digest, although it can bind one or more digests.
3. `Organization` is not an email address, cloud account, tenant ID, billing account, or IdP subject.
4. `Agreement` is not an offer. Acceptance creates or identifies an agreement.
5. `Entitlement` is not payment status and not fulfillment state.
6. `UsageEvent` is observed consumption; `MeterBatch` is an admitted aggregation submitted to a commercial rail.
7. `Settlement` is not gross usage and not entitlement.
8. `Receipt` records a consequence; it does not grant authority to repeat it.

## Core relations

```text
CommercialProduct hasVersion ProductVersion
ProductVersion exposesCapability Capability
CommercialProduct hasPlan Plan
Plan grants Capability
Offer proposes Plan
Offer scopedTo Organization
Agreement accepts Offer
Agreement yields Entitlement
Entitlement authorizes Capability
Entitlement fulfilledBy Fulfillment
UsageEvent measuredFor Entitlement
MeterBatch aggregates UsageEvent
MeterBatch submittedThrough MarketplaceProjection
Settlement reconciles MeterBatch
MarketplaceProjection projects CommercialProduct
Receipt evidences Transition
StandingClaim appliesTo ExactSubject
```

## Public ontology preference

Use public ontology where semantic equivalence is demonstrated. Typical candidates include PROV-O for provenance, ORG for organizations, DCTERMS for document/version metadata, SKOS for controlled concepts, ODRL for rights/policy relationships, QUDT for units, DCAT for catalog concepts, and SHACL for graph constraints. Public vocabulary does not eliminate the need for custom marketplace terms. A vendor-specific `offerId`, entitlement state, certification identifier, or settlement field remains custom until an equivalence proof exists.

## Constraint examples

```text
Entitlement must reference exactly one Agreement.
Agreement must reference an accepted Offer or equivalent admitted commercial event.
MeterBatch must name its unit, aggregation window, source events, and idempotency identity.
MarketplaceProjection must identify the canonical ProductVersion it projects.
StandingClaim(ALIVE) must name execution and verification evidence.
```

A real implementation should encode these as SHACL, formal constraints, property tests, or a combination. The exact formalism is less important than refusing invalid graphs rather than normalizing them silently.

## Extension rule

A marketplace pack may add classes and properties under its own namespace. It may not redefine canonical identity or broaden canonical authority. Extension is lawful when normalization back to the canonical graph is explicit and projection loss is recorded.
