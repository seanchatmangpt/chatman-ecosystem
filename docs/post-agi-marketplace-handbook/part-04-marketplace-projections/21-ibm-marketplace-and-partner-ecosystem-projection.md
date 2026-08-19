# 21. IBM Marketplace and Partner Ecosystem Projection

> **Vendor observation date:** 2026-08-19. IBM catalog, software, container, and Operator publication requirements can evolve independently; re-verify the selected surface.

## IBM is a family of distribution surfaces

IBM illustrates why `Marketplace` should not be modeled as one storefront API. IBM Cloud catalog services, software publication, container distribution, Operator bundles, and partner-program workflows can participate in the same commercial route without sharing one delivery protocol.

The canonical platform should therefore ask two questions separately:

1. Which IBM surface projects the product commercially?
2. Which IBM surface projects the deployment artifact?

## IBM Cloud service projection

IBM documentation for publishing services to the IBM Cloud catalog includes registration, service details, broker or service integration where applicable, pricing plans, validation, approval, and publication.

A broker/service object is a protocol surface. The canonical plan and entitlement remain above it.

```text
Canonical Plan
  → IBM catalog plan projection
  → IBM customer/service observation
  → canonical Entitlement
```

If the product uses a broker API to provision service instances, broker calls enter fulfillment rather than redefining agreement semantics.

## Software and container projection

IBM software/container publication carries artifact identity, version, documentation, validation, and review concerns. The exact image digest must bind to the canonical product version. Publication proves a distribution fact, not a transaction or entitlement fact unless the selected IBM product model explicitly connects them.

## Operator bundles

Operator publication introduces dependency closure: referenced container artifacts may need to be certified or published before the Operator can qualify. That is a graph dependency, not a reason to flatten container and Operator standing into one check mark.

```text
Certified containers
      ↓
Operator bundle
      ↓
IBM/OpenShift validation
      ↓
Publication
```

## Partner admission

Partner Center and product review processes are external admissions. A fully valid Operator bundle can remain BLOCKED on partner or publication state. Conversely, partner enrollment does not prove artifact behavior.

## Commercial mapping

IBM-specific pricing, account, catalog, broker, and publication identifiers map to canonical product/plan/customer objects. If an IBM surface provides distribution without marketplace-native billing, the commercial entitlement can come from another admitted rail rather than being invented from installation.

## Refusals

- `REFUSED:IBM_CATALOG_VISIBILITY_AS_TRANSACTION`
- `REFUSED:BROKER_INSTANCE_AS_AGREEMENT`
- `REFUSED:OPERATOR_WITH_UNADMITTED_CONTAINER_DEPENDENCY`
- `REFUSED:PARTNER_STATUS_AS_RUNTIME_PROOF`
- `REFUSED:DISTRIBUTION_AS_ENTITLEMENT`

## Operational exercise

Build an IBM capability matrix for cloud service, software artifact, container, and Operator distribution. For every row, identify product mapping, commercial right, deployment artifact, vendor review, runtime verifier, and standing. Preserve `N/A` where a commercial primitive does not apply rather than inventing one.
