# 28. The Fortune 5 Buying System

## There is no single buyer

A Fortune 5 sale is not one approval. It is a graph of independent admissions owned by people and systems with different risk, budget, operational, and legal mandates.

Typical vertices include:

```text
Business sponsor
Engineering
Enterprise architecture
Security
Privacy
Legal
Procurement
Finance
Vendor management
Operations / SRE
Data governance
Network / identity teams
```

A technology marketplace can reduce friction in some of these paths, especially procurement and billing, but it does not erase the others.

## Multi-admission sale

A useful abstraction is:

```text
EnterpriseSale =
  BusinessAdmission
  ∩ TechnicalAdmission
  ∩ SecurityAdmission
  ∩ PrivacyAdmission
  ∩ LegalAdmission
  ∩ ProcurementAdmission
  ∩ FinancialAdmission
  ∩ OperationalAdmission
```

The intersection is product- and customer-specific. A low-risk internal utility may require fewer gates; a global platform touching regulated data can require more.

## Parallelize the real graph

Many admissions can run concurrently. Security evidence can be prepared while legal reviews the DPA. Seller marketplace registration can run while engineering implements entitlement adapters. Network design can start while procurement selects the transaction route.

Other edges are truly sequential. A marketplace may require seller approval before Producer Portal access. A customer may require a signed DPA before production data is admitted. A private offer may need a specific buyer account before it can be constructed.

The objective is not to pretend all clocks are compressible. It is to expose the dependency graph so no human waits for an artifact that could have been manufactured earlier.

## Evidence reuse without false transfer

The platform should maintain a reusable evidence graph:

- exact architecture and data-flow views;
- security-control evidence;
- incident and vulnerability processes;
- certifications and their scope/expiry;
- subprocessors;
- regional/data-residency capabilities;
- support and SLA definitions;
- disaster-recovery evidence;
- product/version provenance;
- marketplace standing.

A prior customer approval is not transferable authority. The evidence that supported it may be reused if the subject and freshness still match.

## Marketplace procurement is one route

A buyer can prefer a marketplace because the cloud vendor is already approved, committed spend can be relevant, or procurement has a standardized path. Another buyer may require direct contracting or a reseller. The commercial product should route through the buyer's admitted channel without creating a second entitlement model.

## Refusals

- `REFUSED:SINGLE_CHAMPION_AS_ENTERPRISE_APPROVAL`
- `REFUSED:MARKETPLACE_LISTING_AS_SECURITY_APPROVAL`
- `REFUSED:SOC_REPORT_AS_UNIVERSAL_CONTROL_ACCEPTANCE`
- `REFUSED:PRIOR_CUSTOMER_APPROVAL_TRANSFER`
- `REFUSED:EXTERNAL_REVIEW_CLOCK_AS_ENGINEERING_TASK`

## Operational exercise

Construct the admission DAG for a global enterprise purchase of the platform. Mark owner, evidence, prerequisite, external clock, authority, and completion condition for every gate. Then compute which gates can run in parallel from day one and which genuinely sit on the critical path.
