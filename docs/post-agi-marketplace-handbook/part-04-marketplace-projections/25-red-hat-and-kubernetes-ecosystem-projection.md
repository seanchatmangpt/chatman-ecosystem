# 25. Red Hat and Kubernetes Ecosystem Projection

> **Vendor observation date:** 2026-08-19. Re-verify Red Hat Partner Connect, Preflight, container certification, Operator, and Ecosystem Catalog requirements before publication.

## Certification is a distribution standing

Red Hat and Kubernetes ecosystems expose an important non-equivalence: certified software distribution can be a first-class product capability even when marketplace-native billing is not part of the same rail.

A certified container or Operator therefore proves bounded artifact and compatibility facts. It does not prove customer purchase, entitlement, settlement, or support agreement.

## Container certification

Current Red Hat partner workflows use product listings and Preflight-based certification for container artifacts before publication in the Red Hat ecosystem. Exact image digest matters.

```text
source
  → container digest
  → security/metadata checks
  → Preflight/certification result
  → Ecosystem Catalog publication
```

`latest` cannot be the evidence identity. The certification receipt binds exact digest, product version, tool/version, and external review result.

## Operator projection

An Operator bundle introduces dependency closure. Referenced images must satisfy the required certification/publication rules before the Operator can truthfully claim the expected standing.

```text
Certified image set
      ↓
Operator bundle
      ↓
Operator qualification
      ↓
OpenShift install/upgrade verification
```

A green bundle syntax check is not an install/upgrade proof.

## Commercial rights

A platform may pair Red Hat distribution with an entitlement purchased through AWS, Microsoft, direct contract, or another rail. The runtime must preserve that distinction:

```text
DistributionArtifactStanding ≠ CommercialEntitlementStanding
```

For disconnected environments, entitlement checks cannot assume continuous public API access. The product needs an admitted offline-license or receipted entitlement projection if it promises air-gapped operation.

## Helm and Kubernetes

A Helm chart can be a useful base projection, but OpenShift qualification includes security-context, image, networking, storage, operator, and platform-specific behavior that ordinary Kubernetes does not prove.

## Refusals

- `REFUSED:CERTIFIED_AS_PAID`
- `REFUSED:OPERATOR_REFERENCES_UNADMITTED_IMAGE`
- `REFUSED:LATEST_TAG_AS_CERTIFICATION_SUBJECT`
- `REFUSED:HELM_RENDER_AS_OPENSHIFT_QUALIFICATION`
- `REFUSED:AIR_GAP_WITH_ONLINE_ONLY_ENTITLEMENT`

## Operational exercise

Define one commercial product with three independent rails: marketplace entitlement, Red Hat certified-container distribution, and Operator-based fulfillment. Build the receipt DAG showing how the three converge on one exact product version without using any one rail as evidence for the others.
