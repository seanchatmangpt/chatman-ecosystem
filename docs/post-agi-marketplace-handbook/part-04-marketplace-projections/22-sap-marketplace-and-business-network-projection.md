# 22. SAP Marketplace and Business Network Projection

> **Vendor observation date:** 2026-08-19. Re-verify SAP Store, PartnerEdge, BTP, and solution-specific program requirements for the exact product category.

## Enterprise application context changes the projection

SAP distribution lives inside an enterprise application and partner ecosystem. The buyer may care about SAP Store procurement, SAP PartnerEdge status, BTP integration, tenant/landscape compatibility, implementation support, and an existing SAP commercial relationship as much as raw cloud deployment.

That makes SAP a useful test of canonicality: the product must preserve its identity without pretending every SAP concept is a cloud-marketplace concept.

## SAP Store as commercial surface

Current SAP partner materials describe SAP Store as a marketplace for partner solutions and include both standard/self-service and more negotiated enterprise sales motions. The canonical offer model can support both:

```text
Canonical Plan
  → standard SAP Store offer

Canonical Plan + BuyerScopedDelta
  → negotiated/private enterprise motion
```

The SAP commercial artifact remains a projection of the product rather than a second product catalog owned by the SAP integration team.

## BTP is a runtime/integration surface

A platform may integrate with SAP Business Technology Platform, authenticate against SAP services, consume business APIs, or deploy components into an SAP-centric landscape. Those technical capabilities are distinct from Store listing/transaction state.

```text
SAP Store standing != BTP runtime standing
```

Both can be necessary for a particular enterprise sale, but each has its own evidence.

## Customer identity

SAP customer numbers, subaccounts, tenants, systems, and business-network participants can all be relevant identifiers. None should be promoted to universal organization identity without a proven mapping. A single global enterprise may own many SAP landscapes and procurement entities.

## Partner and solution admission

PartnerEdge participation, solution readiness, integration validation, listing review, and commercial approval are external or partner-program admissions. `ggen` can manufacture the evidence package and listing projection; it cannot manufacture SAP's acceptance.

## Support and change management

SAP-centric Fortune 5 customers commonly require strong compatibility, release, support, migration, and integration-version commitments. Those promises belong in the canonical product lifecycle and support policy, then project into SAP-specific documentation.

## Refusals

- `REFUSED:SAP_STORE_AS_GENERIC_CONTAINER_REGISTRY`
- `REFUSED:BTP_DEPLOYMENT_AS_COMMERCIAL_LISTING`
- `REFUSED:SAP_TENANT_AS_CANONICAL_ENTERPRISE`
- `REFUSED:PARTNER_ENROLLMENT_AS_PRODUCT_QUALIFICATION`
- `REFUSED:UNVERSIONED_SAP_INTEGRATION_PROMISE`

## Operational exercise

Model the same platform as a standalone SaaS product sold through SAP Store and as a BTP-integrated solution for an SAP-heavy enterprise. Identify shared canonical product rights and all SAP-specific extensions: tenant mapping, integration versions, partner gates, support, and procurement motion.
