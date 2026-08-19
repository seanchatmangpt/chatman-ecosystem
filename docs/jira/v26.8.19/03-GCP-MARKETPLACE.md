# GCP Marketplace — SaaS + Kubernetes App Listing

## Backward from finished

platform-console has a live GCP Marketplace SaaS listing. A Fortune 5 buyer with a GCP billing
account subscribes; the platform's real Procurement API client handles the entitlement
approval/creation flow; a Pub/Sub subscriber ingests entitlement lifecycle messages and resolves
them into the same `plan-state.ts` transition every other cloud drives. Usage reports flow
through Service Control's check/report calls, fed by the same real `overage-billing.ts`
aggregation. In parallel, a Kubernetes-app listing exists: the base Helm chart, wrapped as a GCP
Marketplace `Application` custom resource, passes GCP's k8s-app manifest validation with zero
alpha-API violations.

## Real state today

Zero of the SaaS integration exists — no `@google-cloud/*` package appears anywhere in
`package.json`, no Procurement API client, no Pub/Sub subscriber, no Service Control usage
client. `app/lib/entitlement-adapters/gcp.ts` exists (generated, this session) with every method
a stub. The Kubernetes-app path has a real, checked blocker: `k8s/ratelimit.yaml` uses
`networking.istio.io/v1alpha3` (`EnvoyFilter`), and this is confirmed — via
`kubectl get crd envoyfilters.networking.istio.io -o jsonpath='{.spec.versions[*].name}'` against
the live cluster — to be the **only** API version Istio ships for that resource. `Gateway` and
`VirtualService` have graduated to `v1`; `EnvoyFilter` has not and, as of this repo's Istio
version, cannot.

## Backward-chained work items

### 1. GCP Marketplace partner status + Producer Portal access (non-engineering)
- **Finished:** partner status granted via the Marketplace Vendor Application (MVA), Payments
  Center banking/tax registration complete, Producer Portal access granted.
- **Gap:** none of this exists. Business/legal task, and notably the slowest of the three
  clouds' registration processes per the original research (weeks, with Producer Portal access
  itself gated on partner status completing first — a real sequential dependency, not
  parallelizable within GCP's own process even though it can run in parallel with the other two
  clouds' registrations).

### 2. Procurement API + Pub/Sub entitlement listener
- **Finished:** real `@google-cloud/*` SDK client handling entitlement approval/creation, a
  Pub/Sub subscriber consuming entitlement lifecycle messages, both resolving into
  `plan-state.ts`.
- **Gap:** fully net-new — this is the largest single per-cloud item across all three clouds,
  because unlike AWS (which at least has a generated stub interface shape from an existing SDK
  family) and Azure (which reuses the existing auth abstraction), nothing in this repo's
  dependency tree touches GCP today. Estimated 2-6 weeks per the original research.
- **Depends on:** `04-CROSS-CLOUD-FOUNDATION.md` item 1.

### 3. Service Control usage reporting
- **Finished:** a thin client performs Service Control check+report calls, fed by
  `overage-billing.ts`'s existing rollups.
- **Gap:** does not exist. Estimated 3-5 days once item 2's SDK dependency is in place —
  smaller than item 2 because it's a wire client over already-computed data, same pattern as
  AWS's `BatchMeterUsage` and Azure's metering-service client.

### 4. Kubernetes app packaging — the EnvoyFilter blocker
- **Finished (partially not achievable as stated):** the base chart wrapped as a GCP
  `Application` CRD with zero alpha-API violations.
- **Gap, stated precisely rather than optimistically:** the base chart itself is real and
  verified (`helm lint`/`helm template` both pass, all 6 manifests render). But
  `k8s/ratelimit.yaml`'s `EnvoyFilter` resource has **no stable API to migrate to** — this is
  not a code-quality gap closable by more engineering time, it is Istio's own API surface. Two
  honest options, neither a "fix":
  1. **Exclude `ratelimit.yaml` from the GCP-listed chart variant.** The rate-limiting behavior
     it provides (login-route throttling, per `k8s/ratelimit.yaml`'s own header comment) would
     be absent from GCP-listed deployments unless replaced by a GCP-native mechanism (e.g. Cloud
     Armor rate limiting at the load balancer, a different architecture, not a drop-in
     substitute).
  2. **File the alpha-API usage as a disclosed, accepted limitation** with GCP's listing review
     and request an exception, if GCP's process allows one (unconfirmed — not verified against
     GCP's actual exception process in this pass).
  Do not silently attempt option 1 without confirming with the security/product owner that
  dropping login-route rate limiting for the GCP-listed variant is acceptable — that is a real
  security posture change, not a packaging detail.
- **Depends on:** `04-CROSS-CLOUD-FOUNDATION.md` item 2 (chart parameterization) — the
  Application CRD wrapping needs `.Values`-driven config, which does not exist yet (the current
  chart is a static copy, disclosed in `values.yaml`'s header).

### 5. GCP review
- **Finished:** technical + policy review passed.
- **Gap:** not applicable until items 2-4 produce a submittable listing. External clock, not
  compressible.

## What gymact/autofde-lab can actuate here today

Nothing in this ticket. See `05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md`.
