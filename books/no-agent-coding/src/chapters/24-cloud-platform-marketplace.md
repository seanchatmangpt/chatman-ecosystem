# 24. Cloud, Platform, and Marketplace as Projections

**Executive thesis:** AWS, Azure, GCP, Kubernetes, Terraform, internal platforms, and commercial marketplaces should be treated as target geometries, not as the source of enterprise meaning.

## Provider syntax is not the operating model

Cloud APIs and marketplace schemas are powerful but vendor-specific representations. If the enterprise lets each provider define the canonical meaning of entitlement, deployment, identity, cost policy, or capability, multi-cloud strategy becomes repeated translation by people and agents.

## Model the invariant, project the provider

The semantic core can express the provider-independent capability and the provider-specific constraints separately. ggen then manufactures the appropriate target surface. This does not pretend providers are equivalent; it makes differences explicit as bounded projection rules rather than hidden in ad hoc code.

## Standing remains provider-specific

Deterministic manufacture cannot prove that an external provider accepted and realized a consequence. Real cloud, marketplace, or payment claims require observation at the provider boundary and exact-provider receipts. Projection standing and operational standing must remain distinct.

## Operating practice

For a multi-provider capability, define the invariant first, then model each provider’s divergence. Test both the common contract and the provider-specific falsifiers. Never promote successful local generation into a claim about external provider execution.

## Diagnostic question

Which provider-specific representation has accidentally become your enterprise source of truth?
