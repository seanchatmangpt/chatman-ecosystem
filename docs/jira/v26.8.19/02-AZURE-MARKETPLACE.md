# Azure Marketplace — SaaS Offer

## Backward from finished

platform-console has a live, transactable Azure Marketplace SaaS offer. A Fortune 5 buyer with
any Microsoft Entra ID tenant purchases through the commercial marketplace, is redirected to a
real landing page that resolves and activates their subscription against the SaaS Fulfillment
API v2, and authenticates via multi-tenant Entra ID SSO — the same identity used to purchase.
Subscription lifecycle changes (plan change, suspend, unsubscribe, reinstate) arrive at a real
webhook, are handled idempotently, and resolve to the same `plan-state.ts` transition Stripe and
AWS both drive. Metered-billing dimensions post usage events to the Marketplace Metering Service
within 24 hours of consumption, fed by the same real usage rollups `overage-billing.ts`
computes today.

## Real state today

Zero of this exists. No Entra ID (Azure AD) app registration, no Fulfillment API v2 client, no
webhook route, no metering-service client. `app/lib/entitlement-adapters/azure.ts` exists
(generated, this session) with a `verifyWebhookSignature` stub explicitly flagged in its own
header comment as needing a real implementation, not silently left wrong. `app/lib/*`'s existing
OIDC/session modules are real and extensible but have never been pointed at a multi-tenant Entra
app.

## Backward-chained work items

### 1. Partner Center account + program enrollment (non-engineering)
- **Finished:** business profile, tax forms, payout info, and identity/MPN verification
  complete in Partner Center.
- **Gap:** none of this exists. Business/legal task — see `04-CROSS-CLOUD-FOUNDATION.md`.
  Estimated days to a couple of weeks per the original research, run in parallel with
  engineering.

### 2. Multi-tenant Entra ID SSO app registration
- **Finished:** a multi-tenant Entra ID (Azure AD) app registered, accepting sign-in from any
  customer tenant, wired into the platform's existing session/OIDC layer as an additional
  identity provider path (not a replacement for the existing one — customers signing up outside
  the marketplace still use the current flow).
- **Gap:** does not exist. This is the cheapest of the three clouds' identity requirements
  because `app/lib/*`'s auth abstraction is real and designed for exactly this kind of
  extension — estimated 1-3 days, the shortest single item across all three clouds' per-cloud
  work.

### 3. Fulfillment API v2 landing page + webhook
- **Finished:** a real landing route resolves the token AWS-equivalent Azure sends on purchase
  redirect (`Resolve`), calls `Activate`, and a separate webhook route ingests subscription
  lifecycle events, both writing through to `plan-state.ts` and the org-scoped `audit_log`.
- **Gap:** `app/lib/entitlement-adapters/azure.ts`'s stub methods need real bodies against the
  real Fulfillment API v2 REST contract. Estimated ~1.5-2 weeks total for this item plus item 2
  combined — genuinely the cheapest per-cloud integration of the three, per the original
  research, because of the reuse named above.
- **Depends on:** `04-CROSS-CLOUD-FOUNDATION.md` item 1 (`plan-state.ts` extension).

### 4. Metering service integration (only if using metered-usage dimensions)
- **Finished:** a thin client posts batched usage events to the Marketplace Metering Service,
  fed by `overage-billing.ts` / `cost.ts`'s existing aggregation — no new usage-tracking system.
- **Gap:** thin wire client does not exist. Estimated 3-5 days — down from a from-scratch
  estimate specifically because the aggregation logic this depends on already ships.

### 5. Container / Kubernetes app offer (optional, parallel listing type)
- **Finished:** the base Helm chart (`chart/platform-console/`, wrapped and verified this
  session — `helm lint`/`helm template` both pass) packaged as a CNAB via `porter`, image pushed
  through the publisher's ACR to Microsoft's public ACR, vulnerability-scanned.
- **Gap:** no CNAB wrapping exists; the chart is a real static wrap of 6 manifests but is not
  yet `.Values`-parameterized (disclosed in `chart/platform-console/values.yaml`'s header).
  Depends on `04-CROSS-CLOUD-FOUNDATION.md` item 2 (chart parameterization) and item 3 (shared
  scan gate, targeting ACR as one of its two publish destinations — the generated
  `marketplace-scan-publish.yml` already has an ACR stage, unrun, same as AWS's ECR stage).

### 6. Marketplace certification review
- **Finished:** technical + policy review passed on first submission.
- **Gap:** not applicable until items 2-4 exist to submit. Estimated 2-4 weeks if clean on first
  submission, longer with review cycles — this is an external clock (Microsoft's review queue),
  not compressible by any engineering work in this repo. See `00-OVERVIEW.md`'s framing on
  external-clock items.

## What gymact/autofde-lab can actuate here today

Nothing in this ticket. See `05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md`.
