# Primary Vendor References

> **Edition observation date:** 2026-08-19. Vendor documentation is an external, mutable contract surface. Re-verify before implementation or publication.

This book intentionally centralizes primary vendor references so a marketplace pack can bind a source observation date and detect drift.

## AWS Marketplace

- AWS Marketplace Seller Guide — SaaS product requirements and offer/pricing models.
- AWS Marketplace Metering Service API Reference — `ResolveCustomer` and metering operations.
- AWS Marketplace Entitlement Service API Reference — entitlement lookup for applicable SaaS contract models.
- AWS Marketplace Seller Guide — private offers, agreements, and amendments.
- AWS Marketplace seller registration and tax/banking requirements.

**Current-edition caution:** AWS documentation for new SaaS integrations directs sellers toward `CustomerAWSAccountId` and `LicenseArn`; do not build a new canonical customer model around the older `CustomerIdentifier` field.

## Microsoft commercial marketplace

- Microsoft Learn — Plan a test and development SaaS offer.
- Microsoft Learn — SaaS Fulfillment APIs v2.
- Microsoft Learn — Register a SaaS application in Microsoft Entra ID.
- Microsoft Learn — Marketplace metered billing APIs and custom dimensions.
- Microsoft Learn — SaaS offer pricing models and plans.

**Current-edition caution:** Entra service registration for Marketplace API authentication is not the same claim as requiring customer end-user SSO through Entra.

## Google Cloud Marketplace

- Google Cloud — Cloud Commerce Partner Procurement API.
- Google Cloud — Integrate SaaS with Cloud Marketplace.
- Google Cloud — Producer Portal setup.
- Google Cloud — Kubernetes applications packaging and validation requirements.
- Google Cloud Service Control documentation for supported usage-reporting integrations.

## Oracle Cloud Marketplace

- Oracle — Publishing SaaS and application listings in Oracle Cloud Marketplace.
- Oracle — Marketplace pricing, metering, and transaction models.
- Oracle — Private offers and partner publication workflows.

## IBM

- IBM Cloud Docs — Publishing services to the IBM Cloud catalog.
- IBM partner documentation — publishing software and container products.
- IBM Cloud Docs — validating and publishing Operator bundles and certified artifacts.

## SAP

- SAP PartnerEdge — Build and partner program materials.
- SAP Store partner guide — listing and selling partner solutions.
- SAP Business Technology Platform partner integration documentation.

## Salesforce

- Salesforce ISVforce Guide — managed packages.
- Salesforce AppExchange — security review.
- Salesforce License Management App documentation.
- Salesforce Connected App / External Client App security review guidance.

## ServiceNow

- ServiceNow documentation — publishing eligible applications to the ServiceNow Store.
- ServiceNow Technology Partner Program and application certification materials.

## Red Hat

- Red Hat Partner Connect — container certification with Preflight.
- Red Hat Ecosystem Catalog — publishing certified containers.
- Red Hat Operator certification and publication requirements.

## Snowflake Marketplace

- Snowflake documentation — becoming a provider and creating listings.
- Snowflake documentation — public/private listings and paid pricing models.
- Snowflake documentation — monetization eligibility and trial requirements.

## Databricks Marketplace

- Databricks documentation — becoming a Marketplace provider.
- Databricks documentation — listings, shares, access models, and private exchanges.

## Alibaba Cloud Marketplace

- Alibaba Cloud Marketplace Vendor Guide, updated 2026-06-02.
- Alibaba Cloud Marketplace Vendor Application, updated 2026-06-02.
- Alibaba Cloud — Overview of Publishing SaaS Products, updated 2026-06-03.
- Alibaba Cloud — Publish SaaS Products in SPI Mode, updated 2026-06-04.
- Alibaba Cloud — Publish SaaS Products in License Mode, updated 2026-06-04.
- Alibaba Cloud Marketplace Private Offer, updated 2026-06-02.
- Alibaba Cloud Marketplace Co-sell Program, updated 2026-06-02.
- Alibaba Cloud — Background Knowledge Before Publishing SaaS Products, updated 2026-06-03.

## Source admission rule

A vendor reference contributes to `O`; it does not enter `O*` merely because it is official documentation. Admission also requires that the document applies to the exact marketplace program, product type, region, account type, API generation, and observation date being implemented. Where the source is ambiguous or two vendor documents conflict, preserve both observations and classify the mapping `UNKNOWN` until resolved.
