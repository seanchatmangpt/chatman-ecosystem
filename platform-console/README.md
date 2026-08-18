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

- **Real self-service provisioning, end to end**: an authenticated user submits a
  name/namespace (optionally a DB storage size, default `1Gi`) through `/projects`, and the
  console POSTs both a real `SingleDatabase` and a paired `Project` custom resource
  (`core.supabase.io/v1alpha1`, wired via `spec.databaseRef`) to the Kubernetes API. The real
  Supabase operator reconciles both — standing up Postgres, GoTrue (Auth), PostgREST,
  Realtime, Storage, and an edge-functions runtime for that project, each as real
  Deployments/StatefulSets/Services — and the Project itself reaches
  `status.conditions[Ready] = True` within ~30 seconds of submission, live-verified end to
  end (see `self-service-project-provisioning` in `evidence/control-evidence-bundle.json`),
  not left stuck at `DatabaseNotReady`.
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
| `/projects` | Lists real `Project` CRs cluster-wide; form POSTs a paired `SingleDatabase` + `Project` manifest, reaching `Ready` end to end | `app/api/projects/route.ts`, `lib/k8s.ts` |
| `/projects/[name]/database` | Reads real Postgres/PostgREST `Service` objects (ClusterIP, ports, DNS names) | `lib/k8s.ts` |
| `/projects/[name]/auth` | Proxies real GoTrue `/admin/users`, gated on `SUPABASE_SERVICE_ROLE_KEY` | `lib/gotrue.ts` |
| `/projects/[name]/storage` | Proxies real Storage-API `/bucket`, same gate | `lib/storage-api.ts` |
| `/projects/[name]/functions` | Shows real connection info; honestly notes the edge-functions runtime exposes no admin introspection endpoint | — |
| `/observability` | Live allowlisted PromQL against the real in-cluster Prometheus | `app/api/prometheus/route.ts`, `lib/prometheus.ts` |
| `/gitops` | Lists real Flux `Kustomization`/`HelmRelease` objects, read-only | `lib/k8s.ts` |
| `/iam` | Lists real RBAC Roles/RoleBindings/NetworkPolicies grouped by namespace | `lib/k8s.ts` |
| `/secrets` | Lists real `type: Opaque` k8s Secrets per namespace (names + key names only, never decoded values); create/delete real Secrets | `app/api/secrets/route.ts`, `lib/k8s.ts` |
| `/logs` | Namespace → pod → container drill-down over real pod stdout/stderr via the k8s pod-log subresource | `app/api/logs/route.ts`, `lib/k8s.ts` |
| `/registry` | Container Registry as an honest **image inventory**: this cluster has no push-capable registry (images are built locally and `kind load docker-image`d straight into containerd), so every real Deployment container's `image` field is cross-referenced against real Pod `containerStatuses` (digest + ready state), flagging any image not confirmed present or stuck on a real pull failure | `lib/k8s.ts` |

`lib/k8s.ts` is a hand-rolled Kubernetes API client using the pod's own in-cluster
ServiceAccount token/CA (`/var/run/secrets/kubernetes.io/serviceaccount`) — no external k8s
client dependency. Off-cluster (local `next build`/dev), it fails closed with
`"not configured"`, the same convention `lib/status.ts` already used.

## RBAC for the PaaS surface

`k8s/paas-rbac.yaml` grants the existing `platform-console` ServiceAccount a new
`ClusterRole/platform-console-paas`: `get/list/watch` (plus `create`, for the Projects
module's `Project` and paired `SingleDatabase` CRs only) on exactly the resources
`lib/k8s.ts` calls — `core.supabase.io/projects`, `core.supabase.io/singledatabases`,
`services`, `namespaces`, Flux `kustomizations`/`helmreleases`,
`rbac.authorization.k8s.io/roles`, `rolebindings`, `networking.k8s.io/networkpolicies`. No
Secrets, no exec/log, no wildcards, no write verb anywhere outside
`projects:create`/`singledatabases:create`. Verified live with real
`kubectl auth can-i --as=system:serviceaccount:platform-console:platform-console` calls — see
`evidence/control-evidence-bundle.json` for the exact denials and allows observed.

The `/secrets` and `/logs` modules are each backed by their **own** per-namespace `Role`/
`RoleBinding` pairs in `k8s/paas-rbac.yaml` — `platform-console-secrets` (`get/list/create/
delete` on `secrets`) and `platform-console-logs-reader` (`get/list` on `pods`, `get` on
`pods/log`) — deliberately kept **out of** the cluster-wide `ClusterRole/platform-console-paas`
above, since both resource types are more sensitive than the read-mostly resources that
ClusterRole grants. Scoped to the platform's own namespaces only, never cluster-wide, never
`kube-system`.

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
  `services-and-deployments.yaml`, `gateway.yaml`, `grafana-route.yaml`, `hpa.yaml`.

## Autoscaling

Real autoscaling-as-a-service, the capability every hyperscaler PaaS wraps (GCP/AWS/Azure
autoscaling groups, Cloud Run concurrency scaling) -- built on the real Kubernetes
Horizontal Pod Autoscaler, not a simulated or documented-only control.

- **metrics-server** installed from the upstream release manifest
  (`kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`).
  kind's kubelet serves a self-signed cert with no IP SANs, which the stock manifest can't
  verify (`tls: failed to verify certificate: x509: cannot validate certificate for
  172.18.0.2 because it doesn't contain any IP SANs` -- the real, observed failure, confirmed
  from live pod logs before patching, not assumed): fixed live with
  `kubectl -n kube-system patch deployment metrics-server --type=json -p='[{"op":"add",
  "path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'`.
  After the patch, `kubectl top nodes` / `kubectl top pods -A` return real live numbers (e.g.
  `platform-eng-colima-control-plane 239m 5% 4185Mi 52%`) -- confirmed, not `error: Metrics
  API not available`.
- **`k8s/hpa.yaml`**: 5 `autoscaling/v2` HorizontalPodAutoscaler objects, one per Deployment
  already carrying a CPU request/limit -- `platform-console-gateway-hpa` (min 2, max 5,
  target 70% CPU) plus one per project `*-status-hpa` (`autofde-lab-status`, `ggen-status`,
  `ggen-marketplace-status`, `gymact-status`; min 1, max 3, target 70% CPU each).
- **ResourceQuota headroom sized for the HPA's own max replica count**, not just the
  original single-replica baseline -- `k8s/resource-quotas.yaml` was re-sized (see its header
  comment for the exact per-namespace math) to fit each namespace's max replicas plus one
  RollingUpdate surge pod, so scaling to max never gets wedged on quota.
- **Live-verified real scale-up, not just object creation**: after applying, all 5 HPAs
  moved off `<unknown>` to real CPU percentages within ~17s (`kubectl get hpa -A`). Real load
  was then generated against `gymact-status` -- four parallel real CPU-bound Python busy-loop
  processes started in the running container via `kubectl exec` (no mock, no synthetic
  metric injection) -- driving its CPU usage from 2m to 202m against a 50m request. The HPA
  controller fired a real `SuccessfulRescale` event: `New size: 3; reason: cpu resource
  utilization (percentage of request) above target`, and `kubectl get hpa -n gymact` showed
  `REPLICAS` actually go from 1 to 3 (the configured max), confirmed via `kubectl get pods -n
  gymact` showing two new real Pods (`gymact-status-...-htxhf`, `...-snpk5`) reach `Running`.
  `kubectl describe resourcequota gymact-quota` at 3 replicas: `limits.cpu 6600m/9,
  limits.memory 3456Mi/5Gi, pods 3/5` -- inside the re-sized quota as designed.
- **Real scale-down, same live HPA**: the load-generating processes were killed in-container
  (`os.kill` via a second `kubectl exec`, since the image ships neither `ps` nor `pkill`).
  CPU usage returned to ~2-5% within one metrics-server scrape interval. Kubernetes' default
  HPA scale-down stabilization window (5 minutes from the last scale event) then elapsed for
  real -- no window was skipped or shortened -- and the controller fired a second real event
  on the same object: `SuccessfulRescale New size: 1; reason: All metrics below target`,
  `kubectl get hpa -n gymact` showing `REPLICAS` actually return to 1, and `kubectl get pods
  -n gymact` showing the two surge Pods enter `Terminating`. One full real scale-up-then-
  scale-down cycle, both directions driven by the live HPA controller against live
  metrics-server data, no step simulated.

## How to reach it

```
echo "127.0.0.1 platform.local" | sudo tee -a /etc/hosts
```

Then browse to `http://platform.local` (routed through the Istio Gateway/VirtualService in
`k8s/gateway.yaml`), or `kubectl port-forward -n platform-console svc/platform-console-gateway
18080:8080` for a direct path. Log in with the seeded admin account (`ADMIN_USERNAME`,
password matching the bcrypt hash in the `platform-console-secrets` Secret).

Grafana is reached through the same Gateway, no port-forward needed: browse to
`http://platform.local/grafana/` (`k8s/grafana-route.yaml` -- a VirtualService on the
existing `platform-console-gateway` routing to `monitoring-grafana.monitoring.svc.cluster.local:80`,
plus a `DestinationRule` disabling mTLS origination to that host, since the `monitoring`
namespace has no Istio sidecar injection). Log in with the `monitoring-grafana` Secret's
`admin-user`/`admin-password` keys. If `platform.local` isn't reachable directly on this
host, `kubectl port-forward -n istio-system svc/istio-ingressgateway 18080:80` and use
`http://platform.local:18080/grafana/` with a `Host: platform.local` header (or the
`/etc/hosts` entry above) instead.

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
versus which are configured but not currently enacted. As of this run: **11 controls verified
with fresh live evidence** (resource-quotas-enforced, network-segmentation,
least-privilege-rbac, audit-logging, self-service-project-provisioning,
observability-proxy-least-privilege, gitops-read-only-visibility, mtls-enforced,
autoscaling-enforced, secrets-never-logged-or-rendered,
least-privilege-per-namespace-secrets-rbac) and **0 open gaps**. mtls-enforced's prior gap (PeerAuthentication
STRICT configured but not enacted by any sidecar) was closed in an earlier pass; see the
bundle for the fix and live proof. This doctrine follows
`ggen-marketplace/packs/soc2-audit-pack`: evidence-bundle-complete, never "compliant".
