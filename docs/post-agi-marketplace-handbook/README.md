# The Post-AGI Marketplace Engineer's Handbook

## Selling one admitted platform across IaaS, PaaS, SaaS, data, AI, and enterprise marketplaces

This book begins where platform engineering normally ends.

A mature engineering platform can be secure, observable, self-service, policy-enforced, resilient, and portable across runtime targets and still be commercially incomplete. An external enterprise needs to discover the product, procure it through an approved channel, accept terms, obtain an entitlement, receive fulfillment, authenticate, consume measurable value, be billed through the chosen route, reconcile that bill, receive support, upgrade, renew, and terminate without losing evidence.

That is **marketplace engineering**.

The book rejects a Big Three ontology. AWS Marketplace, Microsoft commercial marketplace, Google Cloud Marketplace, Oracle Cloud Marketplace, IBM's catalogs and partner surfaces, SAP Store, Salesforce AppExchange, ServiceNow Store, Red Hat's certified ecosystem, Snowflake Marketplace, Databricks Marketplace, Alibaba Cloud Marketplace, and future sovereign or industry markets are **projections** of a canonical commercial product. They are not the product itself.

The governing construction is:

```text
O → admit → O*
O* → μ → canonical commercial product
canonical commercial product → π_market → marketplace projection
admitted intent + exact authority → BRCE → consequence + receipt
receipt + replay → scoped standing
```

or compactly:

```text
(A, R) = BRCE(π_m(μ(O*)), Authority*)
```

The objective is not identical vendor integrations. The objective is **commercial invariance with explicit projection differences**.

## What this book preserves

- Product identity is canonical; marketplace IDs are mappings.
- Entitlement is distinct from payment, fulfillment, deployment, and login.
- Billing is distinct from settlement and reconciliation.
- A listing is not a successful sale.
- A successful API call is not a verified postcondition.
- Seller registration and vendor review are external admissions, not generated artifacts.
- `UNKNOWN != ALIVE`.
- `UNSUPPORTED != REFUSED`.
- SELECT, CONSTRUCT, and DO remain separate.
- Zero consequential commercial actuation occurs without a receipt.
- Vendor documentation is an observed contract surface that must be re-qualified as it changes.
- One unsupported edge is topology, not proof that the entire marketplace graph failed.

## Running example

The running subject is a platform product that can be delivered as vendor-hosted SaaS, customer-hosted Kubernetes, managed application, container/operator, API, and data/AI capability. The same product graph drives plans, entitlements, metering, deployment packages, security claims, support commitments, listing metadata, and marketplace adapters.

The book deliberately treats generated code and listings as projections. `ggen` manufactures projections; formal admission and tests establish bounded correctness; marketplace gyms falsify state-machine assumptions; BRCE controls consequential operations; receipts and replay establish evidence-backed standing.

## Relationship to the platform-engineering volume

The preceding platform-engineering work builds the secure, self-service, governed runtime and treats the platform as a product. This volume takes the next boundary seriously: the platform must become a **commercial product with portable standing**. The architectural question changes from “can teams use this platform?” to “can another enterprise lawfully buy, operate, account for, and exit this product through its chosen technology market?”

## Scope

This is an engineering and systems book. It models legal, tax, accounting, procurement, and compliance facts where they create system constraints, but it does not manufacture legal opinions, accounting judgments, seller approval, or customer authority. Those remain owned by their proper authorities.

Proceed to [the Preface](preface.md) or the [full Summary](SUMMARY.md).
