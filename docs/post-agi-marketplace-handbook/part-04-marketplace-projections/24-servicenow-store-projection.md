# 24. ServiceNow Store Projection

> **Vendor observation date:** 2026-08-19. Re-verify Store eligibility, Technology Partner Program, scope, and certification requirements for the exact application.

## Scoped application as projection

ServiceNow Store commerce centers on applications installed into customer instances. Current ServiceNow guidance for Store publication requires eligible private scoped applications, participation in the Technology Partner Program, and certification. A global-scope implementation is therefore not merely another package choice; it can be a publication-boundary defect.

## Four independent states

```text
Canonical product standing
Store certification standing
Instance installation standing
Commercial entitlement standing
```

These states can move independently. A package can pass local tests but be awaiting Store certification. A certified Store application can be installed into a test instance without proving a paid enterprise entitlement. A customer can hold contractual rights while an upgrade is temporarily blocked on instance compatibility.

## Instance identity

A ServiceNow instance is a runtime/tenant identity, not the canonical enterprise. An enterprise can operate development, test, production, and acquired-business instances. Customer resolution therefore maps marketplace/customer organization to one or more instance identities.

## Certification as external admission

The Store certification process is an external gate. Engineering should produce a deterministic package, dependency manifest, security evidence, test results, documentation, and exact version identity. ServiceNow's approval remains an observed external fact.

The receipt for Store publication should bind the exact scoped-app version and any certification identifier to the canonical product version. Evidence from a prior version cannot automatically transfer after code, permissions, integrations, or data behavior change.

## Commercial rights outside the instance

Never let instance-local installation state become the only commercial source of truth. The product may be sold through ServiceNow, directly, or through a broader enterprise agreement. Canonical entitlement determines what the customer is allowed to use; the instance reports whether that right has been fulfilled.

## Upgrade lifecycle

ServiceNow platform releases and customer upgrade schedules can create compatibility windows. The commercial lifecycle therefore needs supported platform-version ranges, deprecation policy, migration guidance, and support evidence.

## Refusals

- `REFUSED:GLOBAL_SCOPE_AS_STORE_ELIGIBLE_WITHOUT_EVIDENCE`
- `REFUSED:STORE_CERTIFICATION_AS_BUYER_SECURITY_ACCEPTANCE`
- `REFUSED:INSTANCE_ID_AS_CANONICAL_ORGANIZATION`
- `REFUSED:INSTALLATION_AS_ENTITLEMENT`
- `REFUSED:PRIOR_VERSION_CERTIFICATION_TRANSFER`

## Operational exercise

Take one platform capability and project it as a ServiceNow scoped application. Define package/version identity, customer-instance mapping, certification evidence, commercial entitlement source, installation postconditions, upgrade compatibility, support policy, and the exact states required before the projection can be marked ALIVE.
