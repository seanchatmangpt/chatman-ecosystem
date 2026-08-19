# 29. Vendor Onboarding

## The seller becomes a supplier

Publishing software commercially makes the company itself part of the supply chain. Marketplaces and Fortune 5 procurement teams can require legal-entity identity, tax forms, payout/banking configuration, insurance, support contacts, security materials, privacy documentation, certifications, subprocessors, and partner-program enrollment.

These are not code artifacts, but they should still be represented with exact ownership and evidence.

## Canonical vendor evidence pack

Create a reusable `VendorEvidenceGraph` with objects such as:

```text
LegalEntity
TaxProfile
Bank/PayoutProfile
InsurancePolicy
SecurityCertification
SecurityQuestionnaireEvidence
PrivacyNotice
DPA
SubprocessorRegister
SupportPolicy
BusinessContinuityEvidence
PartnerEnrollment
MarketplaceSellerProfile
```

Each object carries source, owner, effective date, expiry, confidentiality classification, allowed reuse, and external identifiers.

## Reuse is projection, not copy-and-paste

AWS, Microsoft, Google, Oracle, SAP, IBM, Alibaba, and enterprise customers ask overlapping questions but do not use identical forms or definitions. The correct pattern is:

```text
Canonical vendor fact
  → vendor/customer-specific projection
  → external review
  → external acceptance observation
```

For example, a legal-entity name and tax status can feed several registrations. The marketplace-specific seller ID and review outcome remain separate evidence.

## Expiry matters

Insurance certificates, security reports, pen tests, certifications, business licenses, and authorized signatory data change. Admission should include freshness and scope rather than keeping a permanent `approved=true` flag.

A seller profile approved last year can remain valid while a security certificate has expired. Standing is capability-specific.

## Legal content is owned by legal authority

Software can prepare EULA templates, compare marketplace clauses, populate approved variables, and validate that required text is present. It cannot manufacture legal approval from a model-generated draft.

The same boundary applies to tax and accounting judgments. The system stores and projects legally/accountingly admitted facts.

## Business onboarding runs beside engineering

Do not wait for entitlement code to finish before starting seller enrollment, and do not wait for seller review to finish before generating/qualifying code that does not depend on credentials. The threads converge only when live publication or transaction requires both.

## Refusals

- `REFUSED:REPOSITORY_OWNERSHIP_AS_SELLER_AUTHORITY`
- `REFUSED:GENERATED_EULA_AS_APPROVED_TERMS`
- `REFUSED:EXPIRED_VENDOR_EVIDENCE`
- `REFUSED:ONE_MARKET_APPROVAL_AS_ANOTHER_MARKET_APPROVAL`
- `REFUSED:TAX_OR_ACCOUNTING_GUESS_AS_ADMITTED_FACT`

## Operational exercise

Build a vendor evidence inventory for every target marketplace. For each artifact record owner, authoritative source, effective/expiry date, markets that can reuse it, markets requiring a separate review, and whether the blocker is engineering, external approval, or missing authority.
