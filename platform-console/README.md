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
| `/login` | Two independent, additive login paths: the original seeded local-admin form, and a second real **identity federation** form (email/password signup/login against the live GoTrue instance's own user-facing REST API) -- see "Identity federation" below | `app/app/api/auth/gotrue-login/route.ts`, `app/app/api/auth/gotrue-signup/route.ts`, `lib/gotrue-auth.ts`, `lib/session.ts` |
| `/projects` | Lists real `Project` CRs cluster-wide; form POSTs a paired `SingleDatabase` + `Project` manifest, reaching `Ready` end to end | `app/api/projects/route.ts`, `lib/k8s.ts` |
| `/projects/[name]/database` | Reads real Postgres/PostgREST `Service` objects (ClusterIP, ports, DNS names) | `lib/k8s.ts` |
| `/projects/[name]/auth` | Proxies real GoTrue `/admin/users`, gated on `SUPABASE_SERVICE_ROLE_KEY` | `lib/gotrue.ts` |
| `/projects/[name]/storage` | Proxies real Storage-API `/bucket`, same gate | `lib/storage-api.ts` |
| `/projects/[name]/functions` | Shows real connection info (still no admin introspection endpoint exists to list deployed slugs); real **Invoke a function** action POSTs a chosen slug straight to the project's real edge-functions Service and renders the real HTTP status/body/duration that comes back, gated `requireRole(session, "member")` | `lib/functions-api.ts`, `app/api/projects/[name]/functions/invoke/route.ts` |
| `/observability` | Live allowlisted PromQL against the real in-cluster Prometheus | `app/api/prometheus/route.ts`, `lib/prometheus.ts` |
| `/gitops` | Lists real Flux `Kustomization`/`HelmRelease` objects, read-only | `lib/k8s.ts` |
| `/iam` | Lists real RBAC Roles/RoleBindings/NetworkPolicies grouped by namespace | `lib/k8s.ts` |
| `/secrets` | Lists real `type: Opaque` k8s Secrets per namespace (names + key names only, never decoded values); create/delete real Secrets | `app/api/secrets/route.ts`, `lib/k8s.ts` |
| `/logs` | Namespace → pod → container drill-down over real pod stdout/stderr via the k8s pod-log subresource | `app/api/logs/route.ts`, `lib/k8s.ts` |
| `/registry` | Container Registry as an honest **image inventory**: this cluster has no push-capable registry (images are built locally and `kind load docker-image`d straight into containerd), so every real Deployment container's `image` field is cross-referenced against real Pod `containerStatuses` (digest + ready state), flagging any image not confirmed present or stuck on a real pull failure | `lib/k8s.ts` |
| `/backups` | Database Backups (RDS/Cloud SQL/Cloud Spanner automated-backup equivalent) for the real `demo-db-postgres` StatefulSet: "Run backup now" creates a real `batch/v1` Job that runs `pg_dump` against the database's real Service, using the exact image and password Secret/key read live off the source Pod's own spec; the dump lands on `platform-backups-pvc`. PVC contents aren't directly queryable via the k8s API, so the Job listing itself (name encodes the timestamp, real completion status, real duration) *is* the backup inventory. **Restore** (the RDS/Cloud SQL point-in-time-restore equivalent): "Restore" next to any `Complete` backup, gated behind a type-the-backup-name-to-confirm step (enforced server-side, not just a disabled button), creates a real `batch/v1` Job that mounts the same PVC read-only, locates that backup's real dump file, clears the target's real table data (`TRUNCATE` per table -- not `DROP SCHEMA`, since the same credential createBackupJob discovers is not a superuser and owns none of the real schemas here; see the module doc in `lib/k8s.ts`), then replays the dump via `psql -f`. Real, disclosed limitation: a plain `pg_dump` with no FK-aware ordering can leave a same-run child-table row unrestored when its parent lands later in the file (observed live, see the evidence bundle) -- the primary data (e.g. a deleted user's own row) restores correctly; dependent rows loaded out of FK order do not, in the same restore pass | `app/api/backups/route.ts`, `lib/k8s.ts` (`createBackupJob`, `createRestoreJob`) |
| `/api-gateway` | Documentation/visibility only -- the real control is enforced entirely by Istio (see "Rate limiting" below); this page just states the configured limit and points to `k8s/ratelimit.yaml` | (static; enforcement in `k8s/ratelimit.yaml`) |
| `/usage` | Cost & Usage (AWS Cost Explorer / GCP Billing Reports / Azure Cost Management equivalent, deliberately **without** any payment processor or currency): real live per-namespace CPU/memory usage from `metrics.k8s.io` (the same source `kubectl top pods` reads) against the real `ResourceQuota` hard `limits.cpu`/`limits.memory` ceiling, with a plain percentage-of-quota figure -- never a dollar amount | `lib/k8s.ts` (`getResourceUsage`, `getResourceQuota`) |
| `/alerts` | Alerting (CloudWatch Alarms / GCP Alerting Policies / Azure Monitor Alerts equivalent): real current alert state read live from the in-cluster Alertmanager's `/api/v2/alerts`, rendered as a table (alertname, state, severity, namespace, since, summary); shows an honest "0 active alerts" when none are firing rather than fabricating one -- see `alerting-pipeline-verified-live` in `evidence/control-evidence-bundle.json` for the real fired-and-cleared synthetic-rule verification | `app/api/alerts/route.ts`, `lib/alertmanager.ts` |
| `/service-discovery` | Service Discovery (AWS Route53 private hosted zone / GCP Cloud DNS internal zone / Azure Private DNS equivalent) -- **not decorative**: CoreDNS plus real k8s `Service`/`Endpoints` objects already are the cluster's internal DNS layer every other module's cluster-internal URLs depend on. Table across the platform's 6 namespaces: Service, real DNS name (`<svc>.<namespace>.svc.cluster.local`), ClusterIP, ports, and ready/total backing-Pod-IP count read live from the matching `Endpoints` object -- the "does this record actually resolve to something healthy" signal. Live-verified with real `nslookup` from a throwaway pod against 4 services: resolved IPs matched the page's ClusterIPs byte-for-byte, and ready-endpoint counts matched `kubectl get endpoints` exactly -- see `service-discovery-dns-resolves-live` in `evidence/control-evidence-bundle.json` | `lib/k8s.ts` (`listEndpoints`, `listServicesWithEndpoints`) |
| `/feature-flags` | Feature Flags (AWS AppConfig / LaunchDarkly / GCP Feature Flags equivalent), backed by one real k8s `ConfigMap` (`platform-feature-flags`, `platform-console` namespace) -- no external SaaS dependency. Lists current flags, toggles booleans in place, and adds new keys, all via a real RFC 7386 JSON merge patch (or a real create on first write) through the console's ServiceAccount. **Genuinely proven live, not just object-mutation**: `autofde-lab-status` (`services/autofde-lab/app.py`) reads this exact ConfigMap on every `/status` request via a real, fresh Kubernetes API call under its own minimal cross-namespace RBAC grant, and adds a real `process_uptime_seconds` field only while `verbose-status` is `"true"` -- toggling the flag through the authenticated console UI/API was confirmed, via direct external `curl` to the live `autofde-lab-status` Service (not just `kubectl exec`), to make the field appear and then disappear on revert. See `feature-flag-live-toggle-verified` in `evidence/control-evidence-bundle.json` for the exact before/after response bodies. | `app/api/feature-flags/route.ts`, `lib/k8s.ts` (`getConfigMap`, `createOrUpdateConfigMap`), `services/autofde-lab/app.py` |
| `/topology` | Cluster Topology -- a **visualization, not a security control** (recorded in the evidence bundle for consistency with this file's "real vs decorative" practice, not because it enforces anything). deck.gl (`OrthographicView`, not a geospatial `MapView` -- there is no real geography here) rendering the exact same `listServicesWithEndpoints` data `/service-discovery` already shows as a table: one `ScatterplotLayer` node per Service (fill = the same ready/total status vocabulary as `EndpointsBadge`, size = ready-endpoint count), grouped into deterministic per-namespace grid clusters computed in `lib/topology.ts` (no randomness, no force-simulation step -- same input always produces the same layout). `ArcLayer` connections are drawn **only** where a real `NetworkPolicy` ingress rule's `namespaceSelector` names a source namespace (`lib/k8s.ts`'s `listNetworkPolicies` was extended with `ingressFromNamespaces`, parsed from `spec.ingress[].from[].namespaceSelector.matchLabels["kubernetes.io/metadata.name"]`) -- never inferred or fabricated traffic. Live-verified: authenticated `GET /topology` returned 200 with all 12 real Services across 6 namespaces embedded in the hydration payload (`autofde-lab-status`, `demo-db-postgres`, `gymact-status`, `ggen-status`, `ggen-marketplace-status`, `platform-console-gateway`, plus the 6 `demo-project-*` Services), real ClusterIPs matching `service-discovery-dns-resolves-live`'s recorded values byte-for-byte, and exactly 4 real cross-namespace edges (`platform-console` → `autofde-lab`/`gymact`/`ggen`/`ggen-marketplace`, matching `k8s/network-policies.yaml`'s `*-allow-from-platform-console` rules) -- see `topology-visualization-real-data` in `evidence/control-evidence-bundle.json` | `lib/topology.ts`, `components/DeckTopology.tsx`, `lib/k8s.ts` (`listNetworkPolicies`) |
| `/org` | **Application-level RBAC** (AWS IAM Identity Center permission sets / GCP Org Policy / Azure AD role assignments equivalent), layered on top of -- never replacing -- the console's own k8s ServiceAccount RBAC. Owner-only page listing real role assignments (`viewer` < `member` < `owner`) from one real k8s `ConfigMap` (`platform-console-org-roles`, `platform-console` namespace, identifier → role), with a form to change a user's role, itself owner-gated. Before this module every authenticated session got identical full access regardless of provider; `POST /api/projects` is now owner-only, `POST`/`DELETE /api/secrets` and `POST /api/feature-flags` are member+ -- every GET stays open to any authenticated user. See "Application-level RBAC" below and `application-rbac-role-enforced` in `evidence/control-evidence-bundle.json` for the real 403-then-403-then-201 promotion sequence | `lib/authz.ts`, `app/api/org/roles/route.ts`, `app/app/org/page.tsx` |

`lib/k8s.ts` is a hand-rolled Kubernetes API client using the pod's own in-cluster
ServiceAccount token/CA (`/var/run/secrets/kubernetes.io/serviceaccount`) — no external k8s
client dependency. Off-cluster (local `next build`/dev), it fails closed with
`"not configured"`, the same convention `lib/status.ts` already used.

## Identity federation

A second, additive login path (the AWS IAM Identity Center / Azure AD / GCP Identity
Platform equivalent): a real end user authenticates against the live GoTrue (Supabase Auth)
instance already running in this cluster (`demo-project-auth.supabase-demo.svc.cluster.local:9999`),
independent of the single seeded admin account. **Additive, not a replacement** — the
original local-admin path (`app/lib/credentials.ts`, `app/api/login/route.ts`) is unchanged
and still works exactly as before; see `identity-federation-live-verified` in
`evidence/control-evidence-bundle.json` for the real regression check.

- `lib/gotrue-auth.ts` — real server-side calls to GoTrue's real **user-facing** auth REST
  endpoints: `POST /signup` and `POST /token?grant_type=password`, parsing GoTrue's real JWT
  `access_token` response. Deliberately distinct from the pre-existing `lib/gotrue.ts`, which
  is a read-only proxy to GoTrue's *admin* API (`/admin/users`, user counts) gated on
  `SUPABASE_SERVICE_ROLE_KEY`.
- `lib/session.ts`'s session shape now carries an `authProvider: "local-admin" | "gotrue"`
  discriminator. A `"gotrue"` session's `sub` is the real GoTrue user id (a UUID, not a local
  username) and additionally carries the real account's `email`. Both providers mint the same
  kind of app-local HS256 JWT cookie, signed with this app's own `AUTH_SECRET` — a GoTrue
  access token is never passed straight through as this app's session, so every existing
  session consumer (`middleware.ts`, every route handler's `requireActor` helper) keeps
  working unchanged, since they only ever read `session.sub`.
- `app/api/auth/gotrue-login/route.ts` and `app/api/auth/gotrue-signup/route.ts` — call
  GoTrue for real; on success mint this app's own session cookie carrying the
  `authProvider:"gotrue"` marker, same cookie name/flags/TTL as the local-admin path.
  `app/app/login/page.tsx` renders both forms side by side, clearly labeled.
- **One disclosed, real adaptation to this specific cluster**: GoTrue here runs with
  `GOTRUE_MAILER_AUTOCONFIRM=false` and no SMTP server configured at all (confirmed live via
  `GET /settings` → `"mailer_autoconfirm":false`, and the Deployment defines no
  `GOTRUE_SMTP_*` vars), so a real `/signup` genuinely leaves the account unconfirmed and a
  real `/token?grant_type=password` genuinely rejects it with GoTrue's own real
  `{"error_code":"email_not_confirmed"}` — reproduced live before any fix, see the evidence
  bundle. Since no mail transport exists on this cluster to deliver a real confirmation link,
  `signUpWithPassword` completes the confirmation the way an operator would for a mailer-less
  deployment: one real `PUT /admin/users/{id}` call (`{"email_confirm":true}`,
  bearer-authenticated with `SUPABASE_SERVICE_ROLE_KEY`) immediately after a real signup
  succeeds — a real GoTrue admin API call, not a fabricated confirmation.
- `SUPABASE_SERVICE_ROLE_KEY` is now wired into the live Deployment (`k8s/services-and-deployments.yaml`,
  sourced from the `platform-console-secrets` Secret) — previously present in code
  (`lib/gotrue.ts`) but never actually set on the deployed pod, so `/projects/[name]/auth`
  reported "not configured" in every prior pass. It's real: copied from the real
  `demo-project-jwt` Secret's `service-key` in `supabase-demo`, the same JWT this cluster's
  own Supabase operator already issues and uses for admin access to `demo-project-auth`.

## RBAC for the PaaS surface

`k8s/paas-rbac.yaml` grants the existing `platform-console` ServiceAccount a new
`ClusterRole/platform-console-paas`: `get/list/watch` (plus `create`, for the Projects
module's `Project` and paired `SingleDatabase` CRs only) on exactly the resources
`lib/k8s.ts` calls — `core.supabase.io/projects`, `core.supabase.io/singledatabases`,
`services`, `namespaces`, Flux `kustomizations`/`helmreleases`,
`rbac.authorization.k8s.io/roles`, `rolebindings`, `networking.k8s.io/networkpolicies`,
`apps/deployments`, `metrics.k8s.io/pods` (real live per-pod CPU/memory usage, the Cost &
Usage module), `resourcequotas` (the same Cost & Usage module's quota ceiling), and
`endpoints` (the Service Discovery module's "is this DNS record actually resolving to
something healthy" signal -- `services` was already granted here for the Database module,
so only `endpoints` was a new grant, confirmed via `kubectl auth can-i list endpoints
--as=system:serviceaccount:platform-console:platform-console` returning a real `no` before
the change). No Secrets, no exec/log, no wildcards, no write verb anywhere outside
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

## Application-level RBAC

Everything above this point is **k8s-level** RBAC: what the console's own `ServiceAccount`
identity may do against the Kubernetes API. Before this module, every authenticated *human*
session -- local-admin or gotrue -- got the exact same full access to every mutating route,
because the app had no authorization model of its own beyond "is logged in". `lib/authz.ts`
adds a real, simple **application-level** RBAC layer (the AWS IAM Identity Center permission
sets / GCP Org Policy / Azure AD role assignments equivalent) on top of -- never replacing --
that k8s-level RBAC: it never grants the ServiceAccount any new Kubernetes permission, it
only gates which authenticated app user may trigger the console into exercising a permission
the ServiceAccount already has.

- **Role model**: `viewer` < `member` < `owner`, stored in one real k8s `ConfigMap`
  (`platform-console-org-roles`, `platform-console` namespace), identifier (email for gotrue
  users, `admin` for the local-admin account) → role. Reuses the exact
  get-then-create-or-patch primitive the Feature Flags module already established
  (`getConfigMap` / `createOrUpdateConfigMap`, a real RFC 7386 JSON merge patch) -- no new
  k8s resource kind, and zero RBAC YAML changes were needed: the existing
  `platform-console-feature-flags` `Role` already grants `get/list/create/update/patch` on
  *all* `configmaps` in the `platform-console` namespace with no `resourceNames`
  restriction, so it already covered this second ConfigMap. `admin` is seeded as `owner` the
  first time the ConfigMap is read if it doesn't exist yet; any identifier with no explicit
  entry defaults to `viewer` (fail-closed -- a brand-new gotrue signup starts at the lowest
  privilege until an owner promotes them).
- A ConfigMap `data` key must match `[-._a-zA-Z0-9]+` -- an email's `@` isn't legal in a key,
  so `lib/authz.ts` escapes any disallowed character as `-xHH-` (its hex code point) and
  reverses it on read; `admin` and plain identifiers round-trip unchanged.
- **`requireRole(session, minimumRole)`** (`lib/authz.ts`): the real server-side gate every
  role-bound route calls after its existing `requireActor`/401 check. A session whose role
  doesn't meet `minimumRole` gets a real `403` with a clear `reason` string naming both the
  actual and required role -- same fail-closed convention as this app's existing `401`s.
- **Wired into 3 real mutating routes, chosen for real consequence**: `POST /api/projects`
  (owner-only -- creating infrastructure), `POST`/`DELETE /api/secrets` (member+ -- managing
  app config, not infrastructure), `POST /api/feature-flags` (member+). Every `GET` stays
  open to any authenticated user regardless of role, per the design.
- **`/org`** (`app/app/org/page.tsx`): an owner-only page listing the real role assignments
  with a form to change one, itself gated by the same `requireRole(session, "owner")` inside
  its backing route (`app/app/api/org/roles/route.ts`) -- the route-level `403` is the real
  enforcement boundary regardless of what the page renders or what the nav shows.
- See `application-rbac-role-enforced` in `evidence/control-evidence-bundle.json` for the
  real, live proof: a fresh GoTrue signup defaulted to `viewer` with no ConfigMap entry
  needed, a real `POST /api/projects` as that session returned a real `403`, the user was
  then explicitly set to `viewer` and re-tested (`403` again), promoted to `owner` via the
  real `/org`-backing route, and the *same* session cookie's next `POST /api/projects`
  returned a real `201` -- RBAC is resolved per-request from the live ConfigMap, not baked
  into the session JWT, so no re-login was needed after promotion.

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
  `resource-quotas.yaml`, `network-policies.yaml`, `mtls.yaml`, `feature-flags.yaml`,
  `services-and-deployments.yaml`, `gateway.yaml`, `grafana-route.yaml`, `hpa.yaml`,
  `ratelimit.yaml`.

## Rate limiting

Real API Gateway throttling -- the AWS API Gateway / GCP Cloud Endpoints / Azure API
Management rate-limit primitive -- implemented via Istio's local rate limit filter
(`envoy.filters.http.local_ratelimit`, token bucket), enforced in-process at the real
`istio-ingressgateway` data plane. No external dependency (no Redis, no global-ratelimit
service): the bucket lives in the gateway's own Envoy worker.

`k8s/ratelimit.yaml` defines two `EnvoyFilter` objects (namespace `istio-system`,
`workloadSelector: {istio: ingressgateway}`):

- `filter-local-ratelimit-svc` installs the `local_ratelimit` HTTP filter into the ingress
  gateway's filter chain with no `token_bucket` configured -- a no-op everywhere by default.
- `filter-local-ratelimit-platform-console-route` merges a `typed_per_filter_config`
  override (`max_tokens: 20, tokens_per_fill: 20, fill_interval: 60s` -- 20 requests/minute)
  onto exactly one Envoy route, matched by `routeConfiguration.vhost.route.name`.

Scoping was deliberate, not blanket: `kubectl get virtualservice -A` showed the shared
`platform-console-gateway` (host `platform.local`) also carries `grafana-route`
(`/grafana/*`). The `platform-console-ingress` VirtualService's catch-all `/` route was given
an explicit name, `platform-console-root` (`k8s/gateway.yaml`), confirmed live via
`istioctl proxy-config routes deploy/istio-ingressgateway -n istio-system` before the
EnvoyFilter was written, so only that one route carries the rate limit -- Grafana traffic on
the identical gateway/vhost is untouched.

**Load-test verification (real, not simulated)**: through
`kubectl port-forward -n istio-system svc/istio-ingressgateway 18080:80` with a
`Host: platform.local` header (same access path as the Grafana-route verification), a tight
loop of 35 sequential `curl` requests against `/` returned `307` (unauthenticated redirect,
the real response) for the first 20 requests, then real `429 Too Many Requests` for all 15
remaining -- the exact `max_tokens: 20` boundary. A follow-up 25-request burst captured the
25th response in full:

```
HTTP/1.1 429 Too Many Requests
x-local-rate-limit: true
content-length: 18
content-type: text/plain

local_rate_limited
```

During that same burst, `/grafana/` on the identical gateway/vhost returned `302` on every
one of 8 requests -- proving the limit is scoped to `platform-console-root` only. After
waiting 65s (past the 60s `fill_interval`), a follow-up request to `/` returned `307` again --
real token-bucket refill. Full evidence: `rate-limiting-enforced` in
`evidence/control-evidence-bundle.json`. Live documentation: `/api-gateway` on the console
itself.

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

## Feature Flags

Real Feature-Flags-as-a-service (AWS AppConfig / LaunchDarkly / GCP Feature Flags
equivalent), backed entirely by one real Kubernetes `ConfigMap`
(`platform-feature-flags`, `platform-console` namespace) -- no external SaaS
dependency, no separate flag-evaluation service.

- **`lib/k8s.ts`**: `getConfigMap(namespace, name)` (returns `{ ok: true, data: null }`
  when not yet provisioned, same convention as `getBackupsPvc`); `createOrUpdateConfigMap`
  does a real get-then-update-or-create -- an existing ConfigMap is updated with a real
  RFC 7386 JSON merge patch (`Content-Type: application/merge-patch+json`), which merges
  recursively into the `data` map, so writing one flag never touches any other flag
  already present; a missing ConfigMap is created fresh instead.
- **`/feature-flags` + `/api/feature-flags`**: lists current flags (name, value), toggles
  a `"true"`/`"false"` flag with one click, and supports adding/editing arbitrary string
  flags -- all through the authenticated console session, same auth/audit-log pattern as
  every other mutating route in this app.
- **RBAC** (`k8s/paas-rbac.yaml`, "Feature Flags" section): two separate least-privilege
  grants, deliberately kept out of the cluster-wide `ClusterRole/platform-console-paas`.
  (1) The console's own ServiceAccount gets `get/list/create/update/patch` on `configmaps`,
  scoped to the `platform-console` namespace only -- never cluster-wide, no `delete`. A
  real bug was caught live during verification: the RBAC `update` verb does **not** cover
  the Kubernetes API's `PATCH` HTTP method (that needs the separate `patch` verb) -- the
  first toggle attempt through the real API returned a real `403`
  (`cannot patch resource "configmaps"`), confirmed via the exact error body, then fixed by
  adding `patch` to the Role and re-verified. (2) `autofde-lab-status`'s own ServiceAccount
  (`autofde-lab-status-reader`, `autofde-lab` namespace) is granted `get` on exactly the
  single named object `platform-feature-flags` (`resourceNames: ["platform-feature-flags"]`)
  via a Role that lives in `platform-console`'s namespace (RBAC Roles only ever authorize
  objects in their own namespace) bound to a cross-namespace subject -- a normal, supported
  RBAC pattern.
- **Why a live k8s-API read, not a ConfigMap-volume mount, for the live-toggle proof**:
  `platform-feature-flags` lives in `platform-console`'s namespace while `autofde-lab-status`'s
  Pods run in `autofde-lab` -- a ConfigMap volume can only ever mount an object from the
  Pod's OWN namespace (a hard Kubernetes constraint), so a genuinely live cross-namespace
  toggle is only reachable via the Kubernetes API. `services/autofde-lab/app.py` makes a
  fresh, uncached HTTPS call to the real API server (using its own in-cluster
  ServiceAccount token/CA, the exact same pattern `lib/k8s.ts` uses) on every single
  `/status` request, and adds one additional real field, `process_uptime_seconds`
  (`time.monotonic()`-derived, never fabricated), only when `verbose-status` reads
  `"true"`. Any read failure fails closed to the baseline response with no extra field.
  One disclosed consequence: propagation is effectively instantaneous (a live read on every
  request), not governed by kubelet's ~60s ConfigMap-volume sync/cache window a mount would
  have had -- a stronger real-time guarantee than the mount approach, not the same as it.
- **Live-verified end to end, real bug included**: see `feature-flag-live-toggle-verified`
  in `evidence/control-evidence-bundle.json` for the full transcript -- baseline `/status`
  (no extra field) -> toggle to `"true"` through the real authenticated console API ->
  `/status` gains a real, live `process_uptime_seconds` (confirmed via both `kubectl exec`
  and a direct external `curl` through `kubectl port-forward` to the real `Service`) ->
  toggle back to `"false"` -> field disappears, confirmed the same two ways.

## How to reach it

```
echo "127.0.0.1 platform.local" | sudo tee -a /etc/hosts
```

Then browse to `http://platform.local` (routed through the Istio Gateway/VirtualService in
`k8s/gateway.yaml`), or `kubectl port-forward -n platform-console svc/platform-console-gateway
18080:8080` for a direct path. `/login` now shows two independent forms side by side: log in
with the seeded admin account (`ADMIN_USERNAME`, password matching the bcrypt hash in the
`platform-console-secrets` Secret), or sign in / create a real account through the second,
additive **identity federation** form -- see "Identity federation" below.

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
versus which are configured but not currently enacted. As of this run: **23 controls verified
with fresh live evidence** (resource-quotas-enforced, network-segmentation,
least-privilege-rbac, audit-logging, self-service-project-provisioning,
observability-proxy-least-privilege, gitops-read-only-visibility, mtls-enforced,
autoscaling-enforced, secrets-never-logged-or-rendered,
least-privilege-per-namespace-secrets-rbac, registry-visibility-least-privilege,
backup-job-verified-nonempty, rate-limiting-enforced, usage-metrics-real-not-fabricated,
alerting-pipeline-verified-live, service-discovery-dns-resolves-live,
feature-flag-live-toggle-verified, topology-visualization-real-data,
identity-federation-live-verified, application-rbac-role-enforced,
restore-recovers-real-deleted-data, edge-function-invocation-verified) and **1 disclosed
gap** (registry-visibility-least-privilege's image-pull-failure path is real code,
untriggered on this cluster today -- see the bundle). mtls-enforced's prior gap
(PeerAuthentication STRICT configured but not enacted by any sidecar) was closed in an
earlier pass; see the bundle for the fix and live proof. restore-recovers-real-deleted-data
also discloses a real, non-hiding limitation of the restore path itself (a dependent-table
row loaded out of FK order in a single restore pass) rather than only claiming what worked
-- see the bundle. edge-function-invocation-verified closed the /projects/[name]/functions
module's prior disclosed gap (no invocation, connection info only) by deploying one real,
minimal Edge Function through the supabase-operator's own `Function` CRD -- investigated
live rather than guessed, confirmed the operator auto-mounts and rolls the functions
Deployment on a new Function CR with zero manual YAML edits -- and wiring a real,
RBAC-gated invoke path through the console into it. This doctrine follows
`ggen-marketplace/packs/soc2-audit-pack`: evidence-bundle-complete, never "compliant".

`digest` at the bottom of the bundle is a BLAKE3 hash over the bundle's own content, so any
edit to a control's evidence text is detectable. Method, confirmed by reproducing the prior
digest byte-for-byte before this pass changed anything: with `digest.value` set to the empty
string, serialize the whole document with `json.dumps(doc, indent=2, ensure_ascii=False)` plus
one trailing newline, BLAKE3-hash the resulting UTF-8 bytes, then write that hex digest back
into `digest.value`.
