# 27. Additional and Emerging Marketplaces

> **Vendor observation date:** 2026-08-19 for the Alibaba Cloud example. Future-market support remains `UNKNOWN` until an exact contract is admitted and executed.

## The Big Three are instances, not the ontology

An architecture that encodes `aws | azure | gcp` as the universe has already failed commercial portability. Oracle, IBM, SAP, Salesforce, ServiceNow, Red Hat, Snowflake, Databricks, Alibaba Cloud, regional marketplaces, sovereign clouds, industry catalogs, API exchanges, and agent marketplaces expose different commercial geometries.

The extension test is simple: can a new market be added primarily by admitting new semantics and projection rules, without changing canonical product identity or duplicating the entitlement core?

## Alibaba Cloud as a concrete extension test

Current 2026 Alibaba Cloud Marketplace documentation describes multiple SaaS production modes.

**SPI mode** lets Marketplace call a seller-provided service-provider interface to produce/activate SaaS instances after purchase.

**License mode** lets the customer activate the purchased product on the seller's site using marketplace-provided license semantics.

Alibaba also documents an instantiated SaaS model in which purchases create service instances and lifecycle includes creation, renewal, expiry, and release. Product tiers are represented through SKUs and optional billing items. EULA information is part of publication.

These primitives are not AWS `ResolveCustomer`, Microsoft Fulfillment API, or Google Procurement API by another name. They map to the same canonical concepts through a different projection.

```text
Canonical Entitlement
  ├── Alibaba SPI fulfillment projection
  └── Alibaba license activation projection
```

Current Alibaba documentation also supports buyer-specific private offers for eligible Service/SaaS products using a specific customer main UID and separately describes co-sell program participation. Those are commercial/channel extensions, not product identity.

## Sovereign and regional markets

A sovereign marketplace can add hard constraints around seller domicile, data residency, identity federation, settlement currency, cryptographic control, support geography, and disconnected operation.

Commercial projection then becomes a constraint intersection:

```text
AllowedProjection =
  ProductCapabilities
  ∩ MarketplaceCapabilities
  ∩ Residency
  ∩ Sovereignty
  ∩ Contract
  ∩ Authority
```

If the intersection is empty, the truthful result is `UNSUPPORTED` or `BLOCKED`, not a fake adapter.

## Unknown future markets

A marketplace capability descriptor should be data, not an enum baked into business logic. New packs can declare product types, offer semantics, entitlement model, meter model, deployment classes, external approvals, and vendor extensions.

## Refusals

- `REFUSED:BIG_THREE_AS_CLOSED_WORLD`
- `REFUSED:AWS_LIFECYCLE_AS_UNIVERSAL_LIFECYCLE`
- `REFUSED:REGIONAL_AVAILABILITY_AS_SOVEREIGN_COMPLIANCE`
- `REFUSED:EMPTY_PLUGIN_AS_FUTURE_MARKET_SUPPORT`
- `REFUSED:ALIBABA_SPI_AS_GENERIC_WEBHOOK_WITHOUT_MAPPING`

## Operational exercise

Add Alibaba Cloud to the canonical graph without introducing a new entitlement state machine. Then define a hypothetical sovereign marketplace whose customer identity, data, logs, cryptographic keys, and settlement must remain in-country. List the extra constraints and the first live falsifier needed before claiming support.
