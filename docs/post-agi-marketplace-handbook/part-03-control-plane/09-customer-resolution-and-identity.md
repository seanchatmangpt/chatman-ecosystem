# 9. Customer Resolution and Identity

## One enterprise, many identities

Marketplace identity, billing identity, runtime tenant identity, enterprise directory identity, and human user identity solve different problems. Collapsing them is one of the fastest ways to create entitlement and support defects.

An enterprise may purchase through a central cloud account, deploy into multiple workload accounts, authenticate employees with a separate identity provider, and have invoices paid by a parent legal entity. None of those identifiers is automatically the canonical organization.

```text
MarketplaceAccount ↔ Organization ↔ Tenant ↔ Principals
                         ↕
                   BillingAccount
```

The arrows are provenance-bearing links, not equality.

## Customer-resolution workflow

1. Admit the marketplace's purchase identity and its issuer.
2. Resolve a canonical `Organization` through deterministic policy.
3. Create a new organization only when no admitted mapping exists.
4. Bind marketplace account, legal customer, tenant, and billing identities explicitly.
5. Keep end-user authentication separate from purchase identity.
6. Preserve every mapping change as history.

The common temptation is to use an email address as the join key. That fails under employee turnover, aliases, acquisitions, and delegated procurement. Stable vendor account identifiers are better inputs, but they still map to the organization rather than becoming it.

## Purchase identity is not login identity

A Microsoft Marketplace backend can authenticate to marketplace APIs through a publisher-owned Entra application while the SaaS application authenticates customer users through any admitted enterprise IdP. An AWS Marketplace buyer account can purchase the product while individual users authenticate through SAML or OIDC. These are separate trust paths.

Likewise, a Salesforce subscriber org or ServiceNow instance is a fulfillment/tenant identity, not necessarily the legal buying organization.

## Organization changes are first-class

Large enterprises merge, divest, reorganize, move cloud accounts, and centralize procurement. The identity graph must support:

- one organization with many marketplace accounts;
- one marketplace account purchasing several product instances;
- tenant transfer under explicit authority;
- organization merge/split with preserved agreement history;
- billing-parent relationships;
- deprovisioning of human users without deleting commercial evidence.

## Refusals

- `REFUSED:EMAIL_AS_CANONICAL_CUSTOMER`
- `REFUSED:PURCHASER_AS_RUNTIME_ADMIN`
- `REFUSED:TRANSIENT_TOKEN_AS_DURABLE_IDENTITY`
- `REFUSED:UNRECEIPTED_ORGANIZATION_MERGE`
- `REFUSED:TENANT_ID_AS_LEGAL_ENTITY`

## Evidence

A customer-resolution receipt should name the source marketplace identity, canonical organization, mapping policy/version, actor, authority, evidence, and effective time. If the mapping is inferred from insufficient evidence, standing remains `UNKNOWN` and fulfillment should stop before rights are granted to the wrong tenant.

## Operational exercise

Model a Fortune 5 customer that buys through one AWS account, authenticates through Entra ID, deploys three customer-hosted instances into different cloud accounts, and pays centrally. Show which identifiers map to the organization and which remain tenant, principal, or billing identities.
