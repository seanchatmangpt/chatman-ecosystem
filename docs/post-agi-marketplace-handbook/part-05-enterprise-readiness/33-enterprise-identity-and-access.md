# 33. Enterprise Identity and Access

## Identity is a federation, not a login page

Fortune 5 identity combines organization identity, human identity, machine identity, marketplace purchaser identity, groups, roles, delegated administrators, provisioning, and deprovisioning. SAML, OIDC, SCIM, and workload federation solve different parts of the graph.

```text
Organization
  ├── IdP federation
  │     ├── Human principals
  │     └── Groups
  ├── SCIM lifecycle
  ├── Workload principals
  ├── Marketplace accounts
  └── Delegated administrators
```

## Stable subject before email

Email addresses are mutable labels. Authorization should bind to stable IdP subject/object identifiers within an admitted issuer context. Display names and emails remain attributes.

A canonical principal is closer to:

```text
Principal = Organization × IdentityProvider × StableSubject
```

Roles are then granted under explicit policy.

## SAML and OIDC

Both can provide enterprise federation. The product should model issuer, audience/client, subject mapping, claim policy, group/role mapping, key/certificate lifecycle, and break-glass behavior. The marketplace through which the customer purchased the product should not silently select the runtime IdP unless the product's admitted policy says so.

## SCIM and deprovisioning

SCIM can synchronize users and groups, but entitlement to the product remains organization-level commercial state. Removing a user from the enterprise directory should remove that principal's access promptly without terminating the enterprise agreement.

Conversely, commercial cancellation should not require inventing SCIM delete events if the IdP still contains users.

## Workload identity

Machine principals need separate lifecycle, credentials/federation, permissions, and audit. A CI/CD service principal is not a human administrator and should not inherit human session semantics.

## Delegated administration

Large enterprises need customer-owned administrators who can assign roles within their organization. Delegation is bounded authority: org admins can manage their principals, not commercial agreement state, marketplace payouts, or other tenants.

## Marketplace identity remains separate

The central cloud team that buys through AWS or Microsoft may never log into the product. Purchase account, enterprise organization, runtime tenant, and user identities are linked but distinct.

## Refusals

- `REFUSED:EMAIL_AS_IMMUTABLE_SUBJECT`
- `REFUSED:UNVERIFIED_GROUP_AS_ADMIN`
- `REFUSED:MARKETPLACE_PURCHASER_AS_RUNTIME_USER`
- `REFUSED:SCIM_DELETE_AS_CONTRACT_TERMINATION`
- `REFUSED:MACHINE_PRINCIPAL_AS_HUMAN_ADMIN`

## Operational exercise

Design identity for an enterprise that purchases through AWS, uses Entra ID OIDC/SAML for users, SCIM for lifecycle, workload federation for automation, and delegated administrators in three business units. Map every identifier to canonical organization, tenant, principal, role, and marketplace account.
