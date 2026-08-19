# AWS Marketplace — SaaS + Container Listing

## Backward from finished

platform-console has a live, transactable AWS Marketplace SaaS listing. A Fortune 5 buyer finds
it in AWS Marketplace, subscribes through AWS's own billing relationship (no separate PO), and
their entitlement flows through `ResolveCustomer` → the platform's registration redirect URL →
a real `plan-state.ts` transition, identical in shape to a Stripe-originated transition. Usage
is metered nightly via `BatchMeterUsage` against the same real per-namespace rollups
`overage-billing.ts` already computes for Stripe. A container listing exists in parallel,
scanned and published to a Marketplace-owned ECR repo. The AWS Foundational Technical Review
passed, so the listing carries the Qualified Software badge and is eligible for ISV Accelerate
co-sell.

## Real state today

Zero of this exists. Grepping the repo for `BatchMeterUsage`, `ResolveCustomer`,
`GetEntitlements`, or `marketplacemetering` returns no matches — there is no AWS SDK dependency,
no registration redirect route, no SNS/SQS consumer. `app/lib/entitlement-adapters/aws.ts`
exists (generated this session via `ggen-marketplace`'s `marketplace-listing-scaffold-pack`)
but every method is `throw new Error(...)`. No ECR pipeline exists; the container image builds
locally (`platform-console/Dockerfile`) with no vulnerability-scan gate wired into CI.

## Backward-chained work items

Each item states the finished-state artifact, then the real gap.

### 1. Seller registration (non-engineering)
- **Finished:** AWS Marketplace Management Portal seller profile live; tax interview (W-9)
  filed; bank disbursement account on file; KYC cleared (triggered by paid listing + non-US
  bank/EMEA sales).
- **Gap:** none of this exists; it is a business/legal task, not code. See
  `04-CROSS-CLOUD-FOUNDATION.md`'s non-engineering section — start this in parallel with
  engineering, day one, per that ticket's explicit ordering.

### 2. Entitlement/metering integration
- **Finished:** `ResolveCustomer`, `BatchMeterUsage`, `GetEntitlements` implemented against the
  real `@aws-sdk/client-marketplace-entitlement-service` and
  `@aws-sdk/client-marketplace-metering` packages; a registration redirect route
  (`app/api/aws/marketplace/register/route.ts` or equivalent) resolves AWS's POST token into a
  real `plan-state.ts` transition; an SNS/SQS consumer ingests subscription lifecycle
  notifications and writes to the org-scoped `audit_log`.
- **Gap:** `app/lib/entitlement-adapters/aws.ts`'s stub methods need real bodies. This is the
  single largest AWS-specific item — estimated 1-3 weeks per the original marketplace-readiness
  research (`00-OVERVIEW.md`'s prior-pass finding, carried forward), because nothing exists to
  build on beyond the generated interface shape.
- **Depends on:** `plan-state.ts`'s `applyEntitlementEvent(source, event)` extension —
  `04-CROSS-CLOUD-FOUNDATION.md` item 1 — must land first so this doesn't invent a parallel
  state machine.

### 3. Container product listing
- **Finished:** image pushed to an AWS Marketplace-owned ECR repo, passing the mandatory
  vulnerability/malware/EOL-package scan, running non-root with least-privilege by default,
  deployable on ECS/EKS/Fargate.
- **Gap:** no ECR publish step exists anywhere in this repo's CI. The generated
  `.github/workflows/marketplace-scan-publish.yml` (this session, `ggen-marketplace`) has an
  ECR-publish stage shaped correctly but has never run — it references
  `AWS_ECR_PUBLISH_ROLE_ARN`, which does not exist as a GitHub secret. Confirm the existing
  `Dockerfile` already runs as non-root before assuming this item is purely a pipeline problem
  (checked: `platform-console/Dockerfile` — verify `USER` directive is present and non-root
  before marking this item done).

### 4. AMI listing — explicit non-goal
- **Finished (rejected as a goal):** no AMI artifact exists, and this ticket set does not
  propose building one. No Packer/EC2 Image Builder tooling exists anywhere in the repo; the
  product is container-native end to end. Building a parallel AMI distribution mechanism
  duplicates the container path for no buyer-facing gain absent a specific enterprise demand for
  it. Named here so it is not silently reopened as a forgotten gap later.

### 5. AWS Foundational Technical Review (FTR) prep
- **Finished:** FTR question set answered and passed, using real existing controls —
  `k8s/paas-rbac.yaml` (RBAC), `k8s/network-policies.yaml`, `k8s/mtls.yaml`,
  `k8s/admission-policy.yaml` — mapped to AWS's specific FTR questions.
- **Gap:** the controls are real and already shipped; the mapping/documentation exercise has not
  been done. Estimated 40-80 hours, purely a writing task against existing evidence, not new
  engineering.

## Order this ticket cannot violate

Item 2 depends on `04-CROSS-CLOUD-FOUNDATION.md` item 1 landing first (the `plan-state.ts`
extension). Item 3's scan gate depends on `04-CROSS-CLOUD-FOUNDATION.md` item 3 (the shared
CI scan-gate build) landing first — do not build an AWS-only scan pipeline when the shared one
already exists as generated scaffolding.

## What gymact/autofde-lab can actuate here today

Nothing in this ticket. See `05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md` — none of AWS's real SDK
calls, IAM provisioning, or ECR publish steps map onto gymact's closed Castle-verb allowlist or
autofde-lab's plan-projection-only capability.
