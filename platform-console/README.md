# Platform Console

A self-service PaaS control plane deployed on the `kind-platform-eng-colima` cluster: a
Next.js console (`console`) plus four per-project status services
(`autofde-lab-status`, `gymact-status`, `ggen-status`, `ggen-marketplace-status`), behind an
Istio Gateway/VirtualService, with per-namespace NetworkPolicies, least-privilege RBAC, and
per-namespace ResourceQuotas. It provisions and inspects real backing services through the
[Supabase operator](https://github.com/supabase/postgres-operator)-style CRDs (`Project`,
`SingleDatabase`) already installed on the cluster, and reads (never writes) Flux GitOps
objects and cluster RBAC/NetworkPolicy state.

## What "PaaS" concretely means here

This is **not** a claim of hyperscaler-grade infrastructure. It genuinely does not provide
global regions, an SLA, or managed high availability across failure domains — it is a
single-node local `kind` cluster. What it does provide, for real, on that cluster:

- **Real self-service provisioning**: an authenticated user submits a name/namespace through
  `/projects`, the console POSTs a real `Project` custom resource
  (`core.supabase.io/v1alpha1`) to the Kubernetes API, and the real Supabase operator
  reconciles it — standing up Postgres, GoTrue (Auth), PostgREST, Realtime, Storage, and an
  edge-functions runtime for that project, each as real Deployments/StatefulSets/Services.
- **Real multi-tenant isolation**: every project namespace carries a default-deny
  NetworkPolicy plus an explicit allow-rule from `platform-console` only, a STRICT
  PeerAuthentication object (see the mTLS caveat in the evidence bundle — configured, not
  currently enacted by a data-plane proxy), least-privilege RBAC Roles/RoleBindings scoped
  to `get/list/watch` on `pods`/`services` in-namespace only, and a ResourceQuota ceiling.
- **Real read access to the platform's own operational state**: live Prometheus metrics
  (allowlisted PromQL only), live Flux Kustomization/HelmRelease objects, live RBAC/
  NetworkPolicy inventory per namespace.

"GCP/AWS/Azure-level PaaS" is the shape of the surface (a console that provisions backing
services and shows you their state), not a claim of matching their scale, uptime guarantees,
or global footprint.

## Modules

| Route | What it does | Backing evidence |
|---|---|---|
| `/projects` | Lists real `Project` CRs cluster-wide; form POSTs a real Project manifest | `app/api/projects/route.ts`, `lib/k8s.ts` |
| `/projects/[name]/database` | Reads real Postgres/PostgREST `Service` objects (ClusterIP, ports, DNS names) | `lib/k8s.ts` |
| `/projects/[name]/auth` | Proxies real GoTrue `/admin/users`, gated on `SUPABASE_SERVICE_ROLE_KEY` | `lib/gotrue.ts` |
| `/projects/[name]/storage` | Proxies real Storage-API `/bucket`, same gate | `lib/storage-api.ts` |
| `/projects/[name]/functions` | Shows real connection info; honestly notes the edge-functions runtime exposes no admin introspection endpoint | — |
| `/observability` | Live allowlisted PromQL against the real in-cluster Prometheus | `app/api/prometheus/route.ts`, `lib/prometheus.ts` |
| `/gitops` | Lists real Flux `Kustomization`/`HelmRelease` objects, read-only | `lib/k8s.ts` |
| `/iam` | Lists real RBAC Roles/RoleBindings/NetworkPolicies grouped by namespace | `lib/k8s.ts` |

`lib/k8s.ts` is a hand-rolled Kubernetes API client using the pod's own in-cluster
ServiceAccount token/CA (`/var/run/secrets/kubernetes.io/serviceaccount`) — no external k8s
client dependency. Off-cluster (local `next build`/dev), it fails closed with
`"not configured"`, the same convention `lib/status.ts` already used.

## RBAC for the PaaS surface

`k8s/paas-rbac.yaml` grants the existing `platform-console` ServiceAccount a new
`ClusterRole/platform-console-paas`: `get/list/watch` (plus `create`, for the Projects module
only) on exactly the resources `lib/k8s.ts` calls — `core.supabase.io/projects`, `services`,
`namespaces`, Flux `kustomizations`/`helmreleases`, `rbac.authorization.k8s.io/roles`,
`rolebindings`, `networking.k8s.io/networkpolicies`. No Secrets, no exec/log, no wildcards,
no write verb anywhere outside `projects:create`. Verified live with real
`kubectl auth can-i --as=system:serviceaccount:platform-console:platform-console` calls — see
`evidence/control-evidence-bundle.json` for the exact denials and allows observed.

## What's deployed

- 5 project namespaces (`autofde-lab`, `gymact`, `ggen`, `ggen-marketplace`, plus
  `platform-console` itself), each with a default-deny NetworkPolicy, an allow-from-console
  rule, a STRICT PeerAuthentication object, a scoped Role/RoleBinding, and a ResourceQuota.
- `supabase-system` (the Supabase operator) and `supabase-demo` (one real provisioned
  `Project`, `demo-project`, with a paired `SingleDatabase` and all five backing services
  Running).
- `monitoring` (kube-prometheus-stack: Prometheus, Alertmanager, Grafana, kube-state-metrics)
  and `flux-system` (Flux controllers; CRDs installed, no Kustomization/HelmRelease objects
  created yet on this cluster — an honest empty GitOps state, not a fabricated one).
- Manifests applied in order from `k8s/`: `namespaces.yaml`, `rbac.yaml`, `paas-rbac.yaml`,
  `resource-quotas.yaml`, `network-policies.yaml`, `mtls.yaml`,
  `services-and-deployments.yaml`, `gateway.yaml`.

## How to reach it

```
echo "127.0.0.1 platform.local" | sudo tee -a /etc/hosts
```

Then browse to `http://platform.local` (routed through the Istio Gateway/VirtualService in
`k8s/gateway.yaml`), or `kubectl port-forward -n platform-console svc/platform-console-gateway
18080:8080` for a direct path. Log in with the seeded admin account (`ADMIN_USERNAME`,
password matching the bcrypt hash in the `platform-console-secrets` Secret).

For live Grafana access (no ingress exists for it yet):
`kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80`.

## What "revenue-ready" concretely means here

The `/pricing` page (`app/app/pricing/page.tsx`, plan data in `app/data/plans.ts`) exists and
renders three real tiers (Free / Team / Enterprise) with real feature lists. **There is no
checkout flow and no payment processor wired in** — the Free/Team CTAs link to `/login`, and
the Enterprise CTA is a plain `mailto:` link. Wiring an actual payment processor (Stripe or
otherwise) requires the account owner's own payment-processor account and API credentials;
this repo never touches financial credentials or payment integration, by design. "Revenue
ready" here means the pricing surface and tier definitions exist, not that the platform can
currently take payment.

## What "SOC2" concretely means here

`evidence/control-evidence-bundle.json` is an **evidence bundle**, not a SOC 2 report and not
a compliance determination — those can only come from a licensed CPA firm after an
independent audit. It records exactly which technical controls were actually observed
enforced (with real command output as evidence, re-run fresh against the current cluster)
versus which are configured but not currently enacted. As of this run: **7 controls verified
with fresh live evidence** (resource-quotas-enforced, network-segmentation,
least-privilege-rbac, audit-logging, self-service-project-provisioning,
observability-proxy-least-privilege, gitops-read-only-visibility) and **1 gap**
(mtls-enforced: PeerAuthentication STRICT objects are live, but no workload pod in the
cluster currently carries an Istio sidecar to enact them — root cause and live proof are in
the bundle). This doctrine follows `ggen-marketplace/packs/soc2-audit-pack`:
evidence-bundle-complete, never "compliant".
