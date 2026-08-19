# 52. Live Qualification

## Simulation stops where the real market begins

Schema checks, unit tests, formal invariants, contract fixtures, and marketplace gyms can establish strong candidate evidence. ALIVE still requires observed execution against the exact admitted subject and verifier named by the capability claim.

```text
ALIVE(capability, subject) ⇔
  observed_execution
  ∧ verified_postcondition
  ∧ receipt
  ∧ exact_identity
```

## Exact subject capsule

Before live execution pin:

```text
repository/ref/commit
product version
marketplace pack version
adapter version
artifact digest
seller/test account
buyer/test account
vendor product/listing/plan IDs
environment/region
vendor contract observation
verifier
cost ceiling
authority scope
```

Evidence from a different capsule is adjacent, not automatically transferable.

## Qualification ladder

### Static

Ontology, schema, generation determinism, compile/package, and policy checks.

### Behavioral local/gym

Positive/negative fixtures, state-machine properties, chaos, replay, differential testing.

### Vendor sandbox/test environment

Real vendor authentication and API behavior under non-production or approved test product/account.

### Live marketplace

The exact public/private product, buyer path, transaction, publication, or runtime required by the claim.

A sandbox can make `sandbox.entitlement` ALIVE while `production.entitlement` remains UNKNOWN.

## Verify postconditions independently

A successful `CreateOffer`, `Activate`, `BatchMeterUsage`, package-upload, or publication request is an actuator response. Qualification also observes the vendor-side object or customer-visible state through an independent read where possible.

For fulfillment, verify the actual service. For metering, verify vendor acceptance and later reconciliation. For listing, verify the exact published product/version. For entitlement, verify canonical state and vendor agreement mapping.

## External reviews

Seller approval, marketplace certification, security review, or partner status cannot be simulated into ALIVE. They remain BLOCKED until the vendor produces the external outcome.

## Exact-head rule

If code changes after a live run, the prior evidence proves the old subject. Reuse requires proof that the changed source is irrelevant to the capability or a new run.

## Refusals

- `REFUSED:WORKFLOW_EXISTS_AS_EXECUTION`
- `REFUSED:SANDBOX_AS_PRODUCTION_STANDING`
- `REFUSED:OLD_ARTIFACT_EVIDENCE_FOR_NEW_DIGEST`
- `REFUSED:API_SUCCESS_WITHOUT_POSTCONDITION`
- `REFUSED:VENDOR_REVIEW_SIMULATED_AS_APPROVED`

## Operational exercise

Define the minimum real execution required for two claims: `aws.saas.entitlement` and `aws.container.publish`. Then define a third claim for a Microsoft SaaS meter. Each qualification must name exact accounts, product IDs, adapters, verifier, receipts, exclusions, and standing independently.
