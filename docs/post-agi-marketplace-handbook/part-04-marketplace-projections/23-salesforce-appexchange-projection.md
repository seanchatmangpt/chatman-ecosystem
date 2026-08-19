# 23. Salesforce AppExchange Projection

> **Vendor observation date:** 2026-08-19. Re-verify AppExchange packaging, License Management App, Connected/External Client App, and security-review requirements before release.

## Tenant-centric application commerce

Salesforce AppExchange projects the product into an ecosystem centered on subscriber orgs, packages, versions, licenses, security review, installation, and upgrade. Those are not the same objects as a hyperscaler SaaS subscription, even when both are sold as software.

## Managed package identity

Managed packages provide a controlled distribution and upgrade unit. The canonical product binds package and version identifiers:

```text
CommercialProductVersion
  → Salesforce ManagedPackageVersion
  → install into SubscriberOrg
```

Package version is fulfillment artifact identity, not canonical product identity. A product version may have several marketplace projections, and a subscriber org may contain multiple product packages.

## Subscriber org versus enterprise customer

The Salesforce org is a tenant/deployment identity. Large enterprises can own many orgs. The canonical `Organization` therefore maps to one or more subscriber orgs and separately to the legal/commercial buyer.

## Licensing

Salesforce's License Management App can track managed-package lead/license data and package versions. Those observations can feed the canonical entitlement model, but LMA records do not replace the agreement/entitlement graph. If commercial rights are sold outside AppExchange or across multiple channels, canonical entitlement prevents package-local licensing from fragmenting customer truth.

## Security review

AppExchange publication is subject to Salesforce security review. The review can include managed-package code and related integrations such as Connected Apps or External Client Apps depending on the solution.

Security review is a separate standing rail:

```text
Package build → package tests
            ↘ AppExchange security review
            ↘ subscriber runtime qualification
            ↘ commercial entitlement qualification
```

One cannot substitute for another.

## Upgrade and migration

Managed packages are designed for versioned distribution, but product lifecycle still needs compatibility, data migration, permission changes, license continuity, and rollback/support semantics. The marketplace projection should bind upgrade paths to canonical product-version transitions.

## Refusals

- `REFUSED:PACKAGE_INSTALL_AS_PAID_ENTITLEMENT`
- `REFUSED:SUBSCRIBER_ORG_AS_LEGAL_CUSTOMER`
- `REFUSED:LMA_AS_UNIVERSAL_AGREEMENT_SOURCE`
- `REFUSED:SECURITY_REVIEW_BYPASS_BY_EXTERNAL_COMPONENT`
- `REFUSED:PACKAGE_VERSION_WITHOUT_CANONICAL_MAPPING`

## Operational exercise

Model a managed-package product purchased by one enterprise and installed into three Salesforce orgs. Add an upgrade and a license suspension. Map legal organization, subscriber org, package version, agreement, entitlement, user/license quantities, security-review evidence, and fulfillment receipts without collapsing any identities.
