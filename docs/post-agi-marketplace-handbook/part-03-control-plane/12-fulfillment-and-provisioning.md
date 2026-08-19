# 12. Fulfillment and Provisioning

## Rights and reality are different state spaces

A buyer can be entitled to a product while provisioning is queued, failed, partially complete, or waiting for customer input. Treating entitlement and fulfillment as the same state creates impossible support and audit stories.

Fulfillment translates admitted rights into an operationally available service.

```text
(ServiceState, R_f) = μ_f(Entitlement*, Target*, Authority*)
```

The entitlement authorizes the class of service. A separate authority grant authorizes the actual external changes required to create it.

## Fulfillment machine

```text
REQUESTED
  → PLANNED
  → ACTUATING
  → VERIFYING
  → READY

ACTUATING → FAILED → RETRYING
ACTUATING → COMPENSATING → COMPENSATED
READY → DEPROVISIONING → DEPROVISIONED
```

A job reaching `ACTUATING` does not prove service exists. `READY` requires the buyer-visible postcondition: tenant reachable, deployment healthy, expected identities bound, network path available, and required policy enforced.

## Delivery-specific projections

### Vendor-hosted SaaS

Fulfillment can create a tenant, organization, plan assignment, private-network attachment, or initial administrator. The runtime remains seller-owned.

### Customer-hosted Kubernetes or managed application

Fulfillment creates or coordinates resources in a customer-controlled account. Artifact digest, target account, cluster/version constraints, values/configuration, and installation receipt must bind to the entitlement.

### Package ecosystems

Salesforce, ServiceNow, Red Hat Operators, and similar ecosystems may have installation/upgrade state that is separate from marketplace billing. The canonical fulfillment record links them without pretending installation proves entitlement.

## Compensation is explicit

A failed provisioning flow may have created partial resources. Compensation is a new authorized transition, not an exception handler deleting whatever it can find. The receipt must distinguish resources proven absent from resources whose state is UNKNOWN.

## Cancellation and data

Commercial cancellation does not automatically authorize deletion. Retention, export, legal hold, grace periods, and contract terms may keep data or service artifacts alive after entitlement changes.

## Refusals

- `REFUSED:PROVISION_BEFORE_ENTITLEMENT`
- `REFUSED:JOB_START_AS_FULFILLMENT_SUCCESS`
- `REFUSED:UNBOUNDED_COMPENSATION`
- `REFUSED:CANCELLATION_AS_DATA_DELETE_AUTHORITY`
- `REFUSED:UNVERIFIED_READY_STATE`

## Operational exercise

Model two fulfillment paths from the same canonical plan: vendor-hosted SaaS tenant creation and customer-hosted Kubernetes deployment. Share product/entitlement semantics, but define independent target identities, authority, postconditions, compensation, support SLOs, and receipts.
