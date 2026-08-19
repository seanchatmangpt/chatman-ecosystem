# Appendix B — Marketplace Capability Matrix

This matrix is a **schema for qualification**, not a claim that every row is currently supported by every vendor. Each cell should hold a typed standing plus evidence.

| Capability | AWS | Microsoft | Google | Oracle | IBM | SAP | Salesforce | ServiceNow | Red Hat/K8s | Snowflake | Databricks | Alibaba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Seller/partner admission | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Public listing | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Private/buyer-scoped offer | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| SaaS entitlement | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | UNKNOWN | UNKNOWN | UNKNOWN |
| Usage metering | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | UNKNOWN | UNKNOWN | UNKNOWN |
| Marketplace settlement | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | UNKNOWN | UNKNOWN | UNKNOWN |
| Container distribution | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | N/A | N/A | UNKNOWN | N/A | N/A | UNKNOWN |
| Kubernetes/operator packaging | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | N/A | UNKNOWN | N/A | N/A | UNKNOWN |
| Data/AI listing | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | UNKNOWN | UNKNOWN | UNKNOWN |
| Security/certification review | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Co-sell/partner motion | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

## Cell schema

A production matrix should store:

```text
marketplace
capability
canonical_semantic
vendor_semantic
mapping_kind = EQUIVALENT | NARROWER | BROADER | LOSSY | EXTENSION
exact_subject
standing
evidence[]
exclusions[]
last_verified_at
next_falsifier
```

Do not use a check mark as a substitute for this record. A capability may be supported by the vendor but `UNKNOWN` for the product because it has not been implemented or executed. Conversely, a product may implement a feature that a particular marketplace does not expose, yielding `UNSUPPORTED` for that projection without reducing the product's standing elsewhere.

## Closure calculation

For bounded marketplace set `B`:

```text
Core(B) = ⋂ Capabilities(m)
Extension(B) = ⋃ Capabilities(m) - Core(B)
```

This set equation describes vendor surfaces, not product requirements. Product admission intersects those surfaces with product intent, enterprise requirements, cost, evidence, and authority.
