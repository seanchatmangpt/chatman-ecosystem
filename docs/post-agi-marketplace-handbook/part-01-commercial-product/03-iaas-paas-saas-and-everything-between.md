# 3. IaaS, PaaS, SaaS, and Everything Between

## Service models are responsibility geometries

IaaS, PaaS, and SaaS are useful labels, but marketplace products do not live in three clean boxes. The same platform can be sold as vendor-hosted SaaS, a customer-hosted managed application, a Kubernetes package, a container, an API, a data product, an AI model, or a professional service attached to software.

The correct question is not “which acronym is the product?” It is “which responsibilities and rights does this projection assign?”

```text
ServiceModel =
  RuntimeOwner
  × OperationsOwner
  × DataBoundary
  × DeliveryArtifact
  × CommercialRight
  × Meter
  × SupportBoundary
```

Two products can both be called SaaS while differing radically in tenancy, data processing, networking, customer identity, and metering. Conversely, a single commercial product can expose several delivery modes without changing product identity.

## Delivery classes

### Vendor-hosted SaaS

The seller operates the runtime. Marketplace entitlement normally activates access to a seller-managed tenant or organization. Infrastructure cost, availability, incident response, data residency, and support sit primarily with the seller.

### Customer-hosted managed application

The customer owns or controls the target account while the product supplies a managed deployment definition. Commercial entitlement and deployment identity must remain separate because a customer can possess rights while a deployment is absent, failed, or destroyed.

### Container or Kubernetes product

The marketplace distributes artifacts or package metadata. Certification, image scanning, signatures, Helm/Operator compatibility, and upgrade semantics matter. Distribution does not automatically provide marketplace-native entitlement or settlement.

### API or consumption service

The product boundary is an authenticated service operation. The meter may be calls, compute, tokens, transactions, or outcomes, but the unit must be declared independently from the API implementation.

### Data and AI product

The commercial right can be access to a dataset, share, model, application, or governed query surface. Downstream-use and privacy constraints become part of the product graph.

### Professional or managed service

A marketplace can also commercialize human delivery. Here fulfillment includes staffing, acceptance, milestones, and support obligations that cannot be represented as a container lifecycle.

## Hybrid products

A Fortune 5 platform sale commonly combines modes: SaaS control plane, customer-hosted data plane, private connectivity, optional professional onboarding, and usage-based overage. Forcing this into one service-model label loses the boundaries that procurement and operations care about.

The canonical product therefore models multiple `DeploymentClass` and `CommercialRight` objects. Each marketplace projection selects only combinations that the vendor can express and the product can support.

## Failure modes

- `REFUSED:SERVICE_LABEL_AS_ARCHITECTURE` — IaaS/PaaS/SaaS is used instead of explicit responsibilities.
- `REFUSED:PACKAGE_AS_ENTITLEMENT` — possession of a package is treated as a current commercial right.
- `REFUSED:BYOL_AS_MARKETPLACE_NATIVE_COMMERCE` — an external license path is mislabeled as marketplace billing.
- `REFUSED:HYBRID_BOUNDARY_HIDDEN` — seller and customer operational responsibilities are not explicit.

## Operational exercise

Represent one platform under four delivery classes: vendor-hosted SaaS, customer-hosted Kubernetes, API consumption, and managed service. For each, state runtime owner, data owner, fulfillment, entitlement, meter, support, private-network options, termination behavior, and required evidence. The exercise should make clear that the product is invariant while responsibility geometry changes.
