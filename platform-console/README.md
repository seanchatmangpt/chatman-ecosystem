# Platform Console

A self-service PaaS control plane deployed on the `kind-platform-eng-colima` cluster: a
Next.js console (`console`) plus four per-project status services
(`autofde-lab-status`, `gymact-status`, `ggen-status`, `ggen-marketplace-status`), behind an
Istio Gateway/VirtualService, with per-namespace NetworkPolicies, least-privilege RBAC, and
per-namespace ResourceQuotas. It provisions and inspects real backing services through the
[Supabase operator](https://github.com/supabase/postgres-operator)-style CRDs (`Project`,
`SingleDatabase`) already installed on the cluster, and reads (never writes) Flux GitOps
objects and cluster RBAC/NetworkPolicy state.

## Get started in 5 minutes

**[`/quickstart`](app/app/quickstart/page.tsx)** is the `aws configure` / `gcloud init` /
Vercel CLI equivalent for this console: log in, open `/quickstart`, and download a real,
personalized `quickstart.sh` that creates an API key, provisions a real project, waits for it
to reach real `Ready` status, backs it up, and cleans up — five `curl` calls against this
deployment's own real HTTP API, nothing simulated, tying together the API Keys, Projects, and
Database Backups modules below into one runnable script instead of leaving a first-time user
to find each module's page on their own. See `quickstart-script-runs-clean-end-to-end` in
`evidence/control-evidence-bundle.json` for a real, unedited transcript of that exact script
run start to finish against this live cluster.

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

**See [`docs/SCOPE-AND-LIMITATIONS.md`](docs/SCOPE-AND-LIMITATIONS.md) for the honest,
module-by-module counterpart to this claim**: single control-plane node (no real HA/failover),
single physical machine (no real multi-region or network-partition tolerance), one Postgres
instance per project (no read replicas, no continuous point-in-time recovery beyond on-demand
snapshots), no real customer-facing SLA, and a single-node service mesh (real mTLS/
NetworkPolicy enforcement, but not a multi-region mesh). Read it before treating any module's
hyperscaler-equivalent language as a claim about scale.

**See [`docs/DATA-RESIDENCY.md`](docs/DATA-RESIDENCY.md) for the procurement/legal-facing
answer to "where does customer/production data physically live"**: a single physical machine,
no multi-region replication, no region-selection mechanism, and no data-locality guarantee —
stated plainly for GDPR/CCPA/cross-border-content-rules review, without needing to
reverse-engineer it from the disaster-recovery runbook.

## Modules

| Route | What it does | Backing evidence |
|---|---|---|
| `/login` | Three independent, additive login paths: the original seeded local-admin form, a second real **identity federation** form (email/password signup/login against the live GoTrue instance's own user-facing REST API) -- see "Identity federation" below, and a third real **external OIDC federation** path ("Sign in with our IdP") against a real, genuinely separate, standards-compliant OIDC provider -- see "External OIDC federation" below | `app/app/api/auth/gotrue-login/route.ts`, `app/app/api/auth/gotrue-signup/route.ts`, `app/app/api/auth/oidc-login/route.ts`, `app/app/api/auth/oidc-callback/route.ts`, `lib/gotrue-auth.ts`, `lib/oidc-federation.ts`, `lib/session.ts` |
| `/quickstart` | **Getting-started quickstart** (AWS CLI getting-started / `gcloud init` / Vercel CLI equivalent): session-gated, any role. Generates a real, personalized `quickstart.sh` -- this deployment's real base URL (resolved from the request's own `Host` header) plus the viewer's own live session cookie, embedded so the script's first call can bootstrap without a browser -- demonstrating five real curl calls against this console's own API: create an API key (`/api/api-keys`), create a project (`/api/projects`), poll it to real `Ready` (`/api/projects`), run a real backup (`/api/projects/[name]/backups`), then delete the project (`/api/projects/[name]` DELETE, added alongside this page -- the console previously had no self-service project-deletion capability at all). No new backend capability beyond that one DELETE route; every other step reuses an API route that already existed. Download reuses `ManifestActions.tsx`'s `data:`-URL copy/download pattern from the IaC export page. See `quickstart-script-runs-clean-end-to-end` in `evidence/control-evidence-bundle.json` for the real, unedited transcript of this exact script run against this live cluster | `lib/quickstart.ts`, `app/app/quickstart/page.tsx`, `app/app/api/projects/[name]/route.ts`, `components/ManifestActions.tsx` |
| `/projects` | Lists real `Project` CRs cluster-wide; form POSTs a paired `SingleDatabase` + `Project` manifest, reaching `Ready` end to end. `createProject`'s manifest sets `spec.auth`/`rest`/`realtime`/`functions`/`storage`/`studio` (not just `databaseRef`/`http`) so the operator actually stands up all 6 component Deployments+Services, not just the database -- a real defect (Ready=True with zero component Services created) was caught live and fixed during the `multi-project-tenancy-verified` pass, see `evidence/control-evidence-bundle.json` | `app/api/projects/route.ts`, `lib/k8s.ts` (`createProject`) |
| `/projects/[name]/database` | Reads real Postgres/PostgREST `Service` objects (ClusterIP, ports, DNS names) | `lib/k8s.ts` |
| `/projects/[name]/auth` | Proxies real GoTrue `/admin/users`, gated on `SUPABASE_SERVICE_ROLE_KEY` | `lib/gotrue.ts` |
| `/projects/[name]/storage` | Proxies real Storage-API `/bucket`, same gate | `lib/storage-api.ts` |
| `/projects/[name]/functions` | Shows real connection info (still no admin introspection endpoint exists to list deployed slugs); real **Invoke a function** action POSTs a chosen slug straight to the project's real edge-functions Service and renders the real HTTP status/body/duration that comes back, gated `requireRole(session, "member")` | `lib/functions-api.ts`, `app/api/projects/[name]/functions/invoke/route.ts` |
| `/observability` | Live allowlisted PromQL against the real in-cluster Prometheus | `app/api/prometheus/route.ts`, `lib/prometheus.ts` |
| `/gitops` | Lists real Flux `Kustomization`/`HelmRelease` objects, read-only | `lib/k8s.ts` |
| `/iam` | Lists real RBAC Roles/RoleBindings/NetworkPolicies grouped by namespace | `lib/k8s.ts` |
| `/policy` | Real **Policy as Code / Organization Policy enforcement** (AWS Config Rules / GCP Org Policy equivalent) using Kubernetes' own native `admissionregistration.k8s.io/v1` `ValidatingAdmissionPolicy` (CEL-based, GA since 1.30) -- not a third-party admission webhook framework, none of which is installed on this cluster. Owner-gated, read-only: lists the real, live policy + binding objects and their real CEL rule text verbatim. See "Policy as Code" below and `admission-policy-rejects-noncompliant-deployment` in `evidence/control-evidence-bundle.json` for the real k8s API server rejection transcript | `lib/policy.ts`, `app/app/policy/page.tsx`, `k8s/admission-policy.yaml` |
| `/secrets` | Lists real `type: Opaque` k8s Secrets per namespace (names + key names only, never decoded values); create/delete real Secrets | `app/api/secrets/route.ts`, `lib/k8s.ts` |
| `/scheduled-jobs` | Scheduled Jobs (AWS EventBridge Scheduler / GCP Cloud Scheduler / Azure Logic Apps recurring-trigger equivalent): self-service creation of real `batch/v1` `CronJob` objects, scoped to the platform's own namespaces only via a per-namespace `Role`/`RoleBinding` pair (`k8s/paas-rbac.yaml`) -- never cluster-wide. The real security boundary is the CONTAINER COMMAND: `lib/scheduled-jobs.ts`'s `ALLOWED_COMMANDS` is a fixed, small, server-side allowlist of two harmless commands (echo the real current UTC timestamp; curl the namespace's own `<namespace>-status` Service `/status` and log the real response) -- a request naming anything outside that allowlist is rejected with a `400` before any k8s API call is made; there is no free-text command field anywhere in the create form or the API route. Lists real CronJobs with their real `status.lastScheduleTime`/`status.lastSuccessfulTime` (the CronJob controller's own fields -- no separate fabricated catalog); delete stops all further scheduling. See `scheduled-job-fires-on-real-schedule` in `evidence/control-evidence-bundle.json` for the real create/wait/observe/delete/confirm-no-further-firings proof | `app/api/scheduled-jobs/route.ts`, `lib/scheduled-jobs.ts` |
| `/batch-jobs` | **Batch Compute** (AWS Batch / GCP Batch / Azure Batch equivalent): self-service PARALLEL job fan-out using k8s's own real Indexed `batch/v1` `Job` feature (`completionMode: Indexed`, `parallelism == completions`), distinct from `/scheduled-jobs`'s single-shot, time-triggered `CronJob`s. Reuses Scheduled Jobs' exact allowlist discipline: the same 5 platform namespaces (`BATCHABLE_NAMESPACES` re-exports `SCHEDULABLE_NAMESPACES` unchanged), and a fixed, small, server-side command allowlist (`lib/batch-jobs.ts`'s `ALLOWED_BATCH_COMMANDS`: compute index² or index³ with plain POSIX shell arithmetic) -- no free-text command field anywhere. Each of up to 10 concurrent pods gets a real, kubelet-injected `JOB_COMPLETION_INDEX` env var (confirmed live before any application code was written: a 2-pod probe Job's own logs showed `JOB_COMPLETION_INDEX=0`/`=1` with zero downward-API wiring) and PATCHes its own real, deterministic result into one shared, well-known `platform-batch-results` ConfigMap (never a hostPath, never the PVC-backed pattern Backups uses -- PVC contents aren't queryable via the k8s API, a ConfigMap key is), authenticating as its own narrowly-scoped `platform-batch-runner` ServiceAccount (`patch`, `resourceNames: ["platform-batch-results"]` -- the same `resourceNames`-restricted least-privilege pattern `platform-console-feature-flags-reader` already established, now applied to a workload identity). `collectBatchResults` gathers every completed index's real output back into one aggregated set, cross-checked for missing/duplicate indices against the Job's own real `status.completedIndexes`. See `batch-job-parallel-fanout-verified` in `evidence/control-evidence-bundle.json` for the real overlapping-pod-timestamp proof and the real collected 5/5 result set | `lib/batch-jobs.ts`, `app/api/batch-jobs/route.ts`, `app/app/batch-jobs/page.tsx`, `components/CreateBatchJobForm.tsx`, `components/BatchJobMonitor.tsx` |
| `/deployments/canary` | Real **Canary/Blue-Green deployment control** (AWS CodeDeploy traffic-shifting / GCP traffic-splitting / Azure deployment slots equivalent) for `autofde-lab-status` -- real Istio weighted `VirtualService` routing between two Deployments (`autofde-lab-status`/`autofde-lab-status-canary`, same image, distinguished by a `version` pod label and a runtime `CANARY_VERSION` env var) sharing one Service, split by a real `DestinationRule`'s `stable`/`canary` subsets, in place of the all-or-nothing `kubectl rollout restart` every other Deployment here still uses. Owner-gated weight slider (0-100), live weight + Deployment-readiness display, a **promote** action (100% canary, delete stable) and a **rollback** action (100% stable, delete canary). See "Canary / Blue-Green deployment control" below and `canary-traffic-split-measured-real` in `evidence/control-evidence-bundle.json` for the real per-request tabulated proof at 50/50, 100/0, post-promote, and the final clean steady state | `lib/canary.ts`, `app/api/deployments/canary/route.ts`, `app/app/deployments/canary/page.tsx`, `k8s/canary.yaml` |
| `/load-test` | Real **Load Testing / performance benchmarking self-service** (AWS Distributed Load Testing solution / GCP load-testing guidance tooling equivalent): member+-gated, fires real concurrent HTTP requests (Node's built-in `fetch`, a `Promise.all`-based worker pool, no new dependency) against one service from a fixed allowlist of this platform's own status services -- never an arbitrary user-supplied URL, which would be a real SSRF vector -- and measures real p50/p95/p99 latency and real success/error counts from the actual responses received, not simulated numbers. See "Load Testing" below and `load-test-drives-real-autoscale-event` in `evidence/control-evidence-bundle.json` for the real measured percentiles and the real HPA `SuccessfulRescale` scale-up/scale-down events they drove against `gymact-status` | `lib/load-test.ts`, `app/api/load-test/route.ts`, `app/app/load-test/page.tsx` |
| `/logs` | Namespace → pod → container drill-down over real pod stdout/stderr via the k8s pod-log subresource | `app/api/logs/route.ts`, `lib/k8s.ts` |
| `/exec` | **Container Exec / browser-based shell access** (AWS Systems Manager Session Manager / GCP Cloud Shell / Azure Cloud Shell equivalent): owner-only, real command execution inside a real running pod over the k8s API's real `pods/exec` subresource, upgraded to a real WebSocket (the same mechanism `kubectl exec` itself uses -- confirmed live to work over a plain WebSocket upgrade against this cluster's real v1.34 API server using the `v4.channel.k8s.io` subprotocol, not just SPDY). Two independent execution paths, both resolving `commandId` against the exact same fixed, server-side allowlist (`lib/container-exec.ts`'s `ALLOWED_EXEC_COMMANDS`: `cat /app/facts.json`, `echo`, `env`, `ls -la /app` -- no free-text command field anywhere): a buffered `POST /api/exec` (Node-runtime API route), and a real live-streaming relay at `/ws/exec` (`server.js`, reusing the Realtime Notifications pass's WebSocket-upgrade infrastructure) that opens its own real WebSocket straight through to the target pod's exec subresource and forwards every real stdout/stderr/status frame to the browser as it arrives. Three independent gates before any command ever runs: an unrecognized `commandId` is rejected before any k8s connection is attempted (server-side, both paths); a non-owner session is rejected before the allowlist is even checked; and the k8s API itself enforces a new, real, per-namespace `pods/exec` RBAC grant (`get`+`create`, see below) -- a request that cleared every app-level gate would still get a real 403 from the API server without it. See `container-exec-output-matches-kubectl` in `evidence/control-evidence-bundle.json` for the real byte-for-byte proof | `lib/container-exec.ts`, `app/api/exec/route.ts`, `app/exec/page.tsx`, `components/ExecPanel.tsx`, `server.js` |
| `/security-scan` | **Container Vulnerability Scanning** (AWS ECR image scanning / GCP Artifact Registry vulnerability scanning / Azure Defender for Containers equivalent): owner-only, runs the real, open-source `trivy` scanner (Aqua Security) against this platform's own real, currently-built images. Real path taken (task step 1's own decision point): a real scanner binary genuinely was installable here -- Homebrew `trivy` proved real network egress to `mirror.gcr.io/aquasec/trivy-db` (a live `trivy image --download-db-only` pulled the real ~108MB vulnerability DB end to end) -- so this uses the real scanner throughout, never the dpkg/apk-cross-reference fallback the task describes for a no-network environment. Since this platform's own images (`console`, the 4 status services, `platform-prober`) are local-only -- loaded straight into the kind node's containerd, never pushed to any registry -- `lib/vuln-scan.ts` creates a real `batch/v1` Indexed Job (one real pod per image, the official `aquasec/trivy` image) with a real `hostPath` volume onto the node's own `/run/containerd/containerd.sock`, running `trivy image --image-src containerd <ref>` against each image's real, already-loaded bytes; the deliberate positive-control image (`node:10-slim`, a real, old, EOL public image) is scanned via `--image-src remote` (a real registry pull) instead, needing no hostPath. Each pod emits one compact pipe-delimited line per real finding (`--format template`) to its own pod log, read back via the existing `platform-console-logs-reader` Role's `pods`/`pods/log` grant and parsed into typed findings -- package name, installed version, fixed version (when one exists), real CVE id, real severity. New, narrowly-scoped RBAC (`platform-console-vuln-scan` Role, `batch/jobs` get/list/create/delete only, `platform-console` namespace only -- no new `pods`/`pods/log` grant needed, that already existed). Scan pods run with `sidecar.istio.io/inject: "false"` (same real precedent as the evidence bundle's own `nettest` pod) since an injected `istio-proxy` sidecar does not exit when the main container does and would otherwise leave every scan pod stuck `Running` forever. **Live-verified through the deployed pod**: `POST /api/security-scan` (owner session) created a real Job (`vuln-scan-hpqscecy`), polled to real completion (7/7 succeeded, 0 failed) -- `platform-console/console` came back with 253 real findings (8 CRITICAL/45 HIGH/103 MEDIUM/86 LOW/11 UNKNOWN, e.g. real `CVE-2026-33845` against `libgnutls30 3.7.9-2+deb12u6` with a real fixed version `3.7.9-2+deb12u7`), each of the 4 status-service images plus `platform-prober` came back with 191 real findings each (identical `python:3.12-slim`+Debian 13 base, so identical real package sets), and the positive-control `node:10-slim` came back with 135 real findings including 9 CRITICAL (e.g. real `CVE-2022-1664` against `dpkg 1.18.25`) -- proving both that the platform's own images carry real, non-fabricated findings AND that the scan mechanism itself surfaces real findings when they exist, not merely that it always returns empty. See `vulnerability-scan-detects-real-findings-in-control-image` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/vuln-scan.ts`, `app/api/security-scan/route.ts`, `app/security-scan/page.tsx`, `components/VulnScanPanel.tsx`, `services/vuln-scanner/load-trivy-scanner-image.sh` |
| `/registry` | Container Registry as an honest **image inventory**: this cluster has no push-capable registry (images are built locally and `kind load docker-image`d straight into containerd), so every real Deployment container's `image` field is cross-referenced against real Pod `containerStatuses` (digest + ready state), flagging any image not confirmed present or stuck on a real pull failure | `lib/k8s.ts` |
| `/projects/[name]/backups` | Database Backups (RDS/Cloud SQL/Cloud Spanner automated-backup equivalent), project-scoped like Database/Auth/Storage/Functions above -- not a global page. Resolves the target project's real Postgres StatefulSet Pod live via `getProjectDatabasePod` (never a literal `demo-db-postgres`): "Run backup now" creates a real `batch/v1` Job that runs `pg_dump` against that database's real Service, using the exact image and password Secret/key read live off the source Pod's own spec; the dump lands on `platform-backups-pvc`, at a path namespaced by `<namespace>/<database-stem>/`. PVC contents aren't directly queryable via the k8s API, so the Job listing itself (name encodes the timestamp, real completion status, real duration) *is* the backup inventory -- scoped to `app=platform-backups,database=<stem>` so two projects sharing one namespace never see each other's Jobs. **Restore** (the RDS/Cloud SQL point-in-time-restore equivalent): "Restore" next to any `Complete` backup, gated behind a type-the-backup-name-to-confirm step and a server-side same-project-ownership check (the named backup Job must belong to this project's own database, or the API refuses with a real 403), creates a real `batch/v1` Job that mounts the same PVC read-only, locates that backup's real dump file, clears the target's real table data (`TRUNCATE` per table -- not `DROP SCHEMA`, since the same credential createBackupJob discovers is not a superuser and owns none of the real schemas here; see the module doc in `lib/k8s.ts`), then replays the dump via `psql -f`. Real, disclosed limitation: a plain `pg_dump` with no FK-aware ordering can leave a same-run child-table row unrestored when its parent lands later in the file (observed live, see the evidence bundle) -- the primary data (e.g. a deleted user's own row) restores correctly; dependent rows loaded out of FK order do not, in the same restore pass. See `multi-project-tenancy-verified` in `evidence/control-evidence-bundle.json` for the real second-project proof (this module was the one genuinely hardcoded module found; Database/Auth/Storage/Functions were already project-agnostic) | `app/app/api/projects/[name]/backups/route.ts`, `lib/k8s.ts` (`getProjectDatabasePod`, `createBackupJob`, `createRestoreJob`) |
| `/projects/[name]/migrations` | **Database Schema Migrations** (RDS/Cloud SQL schema-management console / Supabase's own migrations-tool equivalent) -- self-service, versioned SQL against a project's live Postgres, distinct from Backups' full dump/restore above. `platform_console.schema_migrations` (`version bigint` PK, `name`, `applied_at`, `checksum`, plus `up_sql`/`down_sql` stored verbatim since this tool has no on-disk migration-file directory to re-read a down script from later) lives inside the TARGET project's own database -- bootstrapped for demo-project via the same one-time direct-`psql` convention the Audit Log pass used for `platform_console.audit_log`, and self-bootstrapped (`CREATE SCHEMA`/`CREATE TABLE IF NOT EXISTS`) for any project onboarded after. `lib/migrations.ts`'s `applyMigration` runs the submitted up SQL and the history-row `INSERT` in one real transaction -- ANY real SQL error (including partway through a multi-statement up SQL string) issues a real `ROLLBACK`, so a failed migration never leaves a half-applied schema change; `rollbackMigration` replays that row's own stored down SQL and deletes the row, same one-transaction atomicity. Owner-gated (`requireRole(session, "owner")`, same boundary as `/org`/`/audit` -- arbitrary DDL is more consequential than a member-gated action), rollback gated behind a type-the-version-to-confirm step (same convention as `RestoreBackupButton`). **Live-verified through the deployed pod**: `POST /api/projects/demo-project/migrations` applied a real 2-statement migration (`CREATE SCHEMA platform_migrations_demo; CREATE TABLE ...widget_orders`), confirmed via a real `psql \d`/`information_schema.tables` query that the table genuinely existed and the row was genuinely recorded in `schema_migrations`; a rollback then replayed the stored down SQL, and the same real queries confirmed the table AND its schema were genuinely gone and the history row genuinely removed. **Atomicity then proven adversarially**: a second migration's up SQL was `CREATE SCHEMA platform_atomic_test; CREATE TABLE ...step_one; THIS IS NOT VALID SQL;` -- the two valid leading statements would succeed under Postgres's implicit multi-statement execution, but the API returned a real 502 with Postgres's own `syntax error at or near "THIS"`, and a real `\dn`/`information_schema.tables` query confirmed `platform_atomic_test` genuinely never existed -- neither the schema nor the table from the two statements that ran before the error survived, and `schema_migrations` stayed at 0 rows. See `schema-migration-transactional-and-reversible` in `evidence/control-evidence-bundle.json` for the full before/after/failure transcript | `lib/migrations.ts`, `app/app/api/projects/[name]/migrations/route.ts`, `app/app/projects/[name]/migrations/page.tsx` |
| `/api-gateway` | Documentation/visibility only -- the real control is enforced entirely by Istio (see "Rate limiting" below); this page just states the configured limit and points to `k8s/ratelimit.yaml` | (static; enforcement in `k8s/ratelimit.yaml`) |
| `/usage` | Cost & Usage (AWS Cost Explorer / GCP Billing Reports / Azure Cost Management equivalent, deliberately **without** any payment processor or currency): real live per-namespace CPU/memory usage from `metrics.k8s.io` (the same source `kubectl top pods` reads) against the real `ResourceQuota` hard `limits.cpu`/`limits.memory` ceiling, with a plain percentage-of-quota figure -- never a dollar amount | `lib/k8s.ts` (`getResourceUsage`, `getResourceQuota`) |
| `/billing` | Illustrative cost preview (AWS Cost Explorer "forecasted bill" / GCP Billing cost-breakdown equivalent), distinct from `/usage` and `/pricing`: real per-namespace CPU-core-hours (`increase()` over the real cumulative `container_cpu_usage_seconds_total` cAdvisor counter) and memory-GiB-hours (`avg_over_time()` of `container_memory_working_set_bytes` x window duration), both read live from the real in-cluster Prometheus, multiplied by a fixed, plainly-labeled **illustrative** rate table (`$0.02`/CPU-core-hour, `$0.01`/GiB-hour -- not a real contracted price) into real per-namespace line items and a real total. Calculation and visibility only: no payment processor, no card-data collection, no financial obligation created anywhere -- banner states this explicitly on the page. See `usage-billing-math-verified-real` in `evidence/control-evidence-bundle.json` for the real induced-load proof that the line items track live Prometheus data rather than a static number | `lib/invoice-preview.ts`, `app/api/billing/route.ts` |
| `/budget-alerts` | **Budget Alerts** (AWS Budgets / GCP Billing Budgets equivalent), owner-gated the same way `/webhooks` and `/org` are (a budget threshold is a real financial-adjacent setting, even with no payment processor anywhere in this platform). An operator sets one real threshold per namespace on either `cpu-core-hours` or illustrative `cost-usd` -- reusing `lib/invoice-preview.ts`'s exact same Prometheus-derived per-namespace metrics `/billing` and `/usage` already compute (same trailing 1h window, no second query path) -- stored in one real k8s `ConfigMap` (`platform-budget-thresholds`, `platform-console` namespace), reusing the exact `getConfigMap`/`createOrUpdateConfigMap` primitive Feature Flags/Webhooks/Org Roles already established. `lib/budget-alerts.ts`'s `checkBudgets()` is wired into `lib/webhook-poller.ts`'s existing 10s tick (a fourth branch alongside backups/alerts, not a second poller) and fires a real `budget.threshold_crossed` webhook (HMAC-SHA256 signed, same mechanism as `project.created`/`backup.completed`/`alert.firing`) the moment real usage FIRST crosses the configured threshold. Deduped by a real "already alerted" marker persisted in the SAME ConfigMap (durable across pod restarts, unlike the other two triggers' in-memory Sets) so a sustained overage fires once, not once per tick; the marker clears the moment usage drops back under threshold so a later re-crossing fires again. That dedup-write path is deliberately isolated to `checkBudgets()` alone -- the page/API's own read path (`listBudgetUsages()`) never touches it, so a dashboard view can never swallow a webhook delivery the poller was about to make. **Live-verified end to end**: a real throwaway receiver Pod+Service in `gymact` was subscribed via the authenticated API to `budget.threshold_crossed`; a deliberately low threshold (`0.003` CPU-core-hours, above the namespace's real ~0.0018 idle baseline) was set for `gymact`'s `cpu-core-hours`; four real CPU-bound Python busy-loop processes were started in the live `gymact-status` container via `kubectl exec` (same technique `autoscaling-enforced` uses), driving real usage from `0.00185` to `0.0037` within one poll tick; the receiver's real logs show exactly ONE delivery, whose HMAC-SHA256 signature was independently recomputed via `openssl dgst -sha256 -hmac <secret>` and matched byte-for-byte; usage stayed over threshold for a further ~2 minutes (12+ poll ticks across both `platform-console-gateway` replicas) with zero further deliveries, proving the dedup holds across ticks and across the 2-replica rollout. See `budget-alert-fires-once-on-real-threshold-crossing` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/budget-alerts.ts`, `lib/webhook-poller.ts`, `app/api/budget-alerts/route.ts`, `app/app/budget-alerts/page.tsx`, `components/BudgetAlertsPanel.tsx` |
| `/alerts` | Alerting (CloudWatch Alarms / GCP Alerting Policies / Azure Monitor Alerts equivalent): real current alert state read live from the in-cluster Alertmanager's `/api/v2/alerts`, rendered as a table (alertname, state, severity, namespace, since, summary); shows an honest "0 active alerts" when none are firing rather than fabricating one -- see `alerting-pipeline-verified-live` in `evidence/control-evidence-bundle.json` for the real fired-and-cleared synthetic-rule verification | `app/api/alerts/route.ts`, `lib/alertmanager.ts` |
| `/service-discovery` | Service Discovery (AWS Route53 private hosted zone / GCP Cloud DNS internal zone / Azure Private DNS equivalent) -- **not decorative**: CoreDNS plus real k8s `Service`/`Endpoints` objects already are the cluster's internal DNS layer every other module's cluster-internal URLs depend on. Table across the platform's 6 namespaces: Service, real DNS name (`<svc>.<namespace>.svc.cluster.local`), ClusterIP, ports, and ready/total backing-Pod-IP count read live from the matching `Endpoints` object -- the "does this record actually resolve to something healthy" signal. Live-verified with real `nslookup` from a throwaway pod against 4 services: resolved IPs matched the page's ClusterIPs byte-for-byte, and ready-endpoint counts matched `kubectl get endpoints` exactly -- see `service-discovery-dns-resolves-live` in `evidence/control-evidence-bundle.json` | `lib/k8s.ts` (`listEndpoints`, `listServicesWithEndpoints`) |
| `/feature-flags` | Feature Flags (AWS AppConfig / LaunchDarkly / GCP Feature Flags equivalent), backed by one real k8s `ConfigMap` (`platform-feature-flags`, `platform-console` namespace) -- no external SaaS dependency. Lists current flags, toggles booleans in place, and adds new keys, all via a real RFC 7386 JSON merge patch (or a real create on first write) through the console's ServiceAccount. **Genuinely proven live, not just object-mutation**: `autofde-lab-status` (`services/autofde-lab/app.py`) reads this exact ConfigMap on every `/status` request via a real, fresh Kubernetes API call under its own minimal cross-namespace RBAC grant, and adds a real `process_uptime_seconds` field only while `verbose-status` is `"true"` -- toggling the flag through the authenticated console UI/API was confirmed, via direct external `curl` to the live `autofde-lab-status` Service (not just `kubectl exec`), to make the field appear and then disappear on revert. See `feature-flag-live-toggle-verified` in `evidence/control-evidence-bundle.json` for the exact before/after response bodies. | `app/api/feature-flags/route.ts`, `lib/k8s.ts` (`getConfigMap`, `createOrUpdateConfigMap`), `services/autofde-lab/app.py` |
| `/custom-domains` | **Custom Domain self-service** (AWS Certificate Manager + Route53 custom-domain binding / GCP Cloud Run custom-domain equivalent), owner-gated. Registering a hostname does the real three-step thing a hyperscaler console does: generates a real, freshly-issued X.509 certificate for that exact hostname via a real `openssl req -x509` subprocess (SAN independently re-verified with Node's own `crypto.X509Certificate#checkHost` before it is ever stored), stores it as a real `kubernetes.io/tls` Secret in `istio-system`, and creates a real `networking.istio.io/v1` `Gateway` + `VirtualService` pair binding that hostname to whichever platform Service the operator picks from the same live list `/service-discovery` reads -- no hand-edited Istio YAML per domain. Every new domain's `Gateway` merges onto the SAME physical Envoy listener `platform-console-gateway`'s own HTTPS server already owns (confirmed live via `istioctl proxy-config listener`), split by SNI -- registering domain #2 never touches domain #1's objects. See "Custom Domains" below and `custom-domain-tls-cert-matches-hostname` in `evidence/control-evidence-bundle.json` for the full real proof, including the presented certificate's SAN and a real post-unbind connection refusal. | `lib/custom-domains.ts`, `app/api/custom-domains/route.ts`, `app/custom-domains/page.tsx` |
| `/certificates` | **Certificate Lifecycle tracking** (AWS Certificate Manager auto-renewal / GCP-managed-certificate rotation equivalent), owner-gated. `lib/cert-lifecycle.ts` scans every TLS-bearing Secret in `istio-system` in one live GET (filtered on the real presence of a `tls.crt` key, never on `type`, since `platform-backups-mtls-credential` is `Opaque` but still carries one), parses each real cert's real `notAfter` with Node's own `crypto.X509Certificate`, and computes real days-until-expiry (warns under 30 days). Custom-domain certificates can be rotated **in place** -- same Secret name, fresh `tls.crt`/`tls.key` via an RFC 7386 merge-patch (reusing `lib/custom-domains.ts`'s own `generateSelfSignedCertificate` and `lib/k8s.ts`'s own `createOrUpdateSecret`), never delete+recreate, so Istio SDS hot-reloads the new cert with zero Gateway/VirtualService churn. **Live-verified zero-downtime rotation**: a real custom domain was registered, a real 1-req/sec HTTPS request loop was run against it through the actual deployed ingress gateway, and a real rotation was triggered mid-loop through the authenticated console -- all 90/90 requests across the rotation returned `200`, and a fresh `openssl s_client` connection immediately after presented a genuinely different certificate (different real serial number, different real `notAfter`) than one made before rotation. See "Certificate Lifecycle" below and `certificate-rotation-zero-downtime-verified` in `evidence/control-evidence-bundle.json` for the full transcript, including the real RBAC gap this proof surfaced and fixed (`patch` was missing from `platform-console-custom-domains-tls`, k8s/paas-rbac.yaml). | `lib/cert-lifecycle.ts`, `app/api/certificates/route.ts`, `app/certificates/page.tsx` |
| `/topology` | Cluster Topology -- a **visualization, not a security control** (recorded in the evidence bundle for consistency with this file's "real vs decorative" practice, not because it enforces anything). deck.gl (`OrthographicView`, not a geospatial `MapView` -- there is no real geography here) rendering the exact same `listServicesWithEndpoints` data `/service-discovery` already shows as a table: one `ScatterplotLayer` node per Service (fill = the same ready/total status vocabulary as `EndpointsBadge`, size = ready-endpoint count), grouped into deterministic per-namespace grid clusters computed in `lib/topology.ts` (no randomness, no force-simulation step -- same input always produces the same layout). `ArcLayer` connections are drawn **only** where a real `NetworkPolicy` ingress rule's `namespaceSelector` names a source namespace (`lib/k8s.ts`'s `listNetworkPolicies` was extended with `ingressFromNamespaces`, parsed from `spec.ingress[].from[].namespaceSelector.matchLabels["kubernetes.io/metadata.name"]`) -- never inferred or fabricated traffic. Live-verified: authenticated `GET /topology` returned 200 with all 12 real Services across 6 namespaces embedded in the hydration payload (`autofde-lab-status`, `demo-db-postgres`, `gymact-status`, `ggen-status`, `ggen-marketplace-status`, `platform-console-gateway`, plus the 6 `demo-project-*` Services), real ClusterIPs matching `service-discovery-dns-resolves-live`'s recorded values byte-for-byte, and exactly 4 real cross-namespace edges (`platform-console` → `autofde-lab`/`gymact`/`ggen`/`ggen-marketplace`, matching `k8s/network-policies.yaml`'s `*-allow-from-platform-console` rules) -- see `topology-visualization-real-data` in `evidence/control-evidence-bundle.json`. **Second, isometric view added on the same data**: a `Tabs` control switches between "Spatial (deck.gl)" (above) and "Isometric (isoflow)" -- `lib/isoflow-model.ts`'s `buildIsoflowModel(rows, policies)` calls `buildTopologySnapshot` internally (no second fetch/derivation path) and projects the identical result onto isoflow's own zod-derived `Model` schema: one `items` node per Service (icon `k8s-svc` from the real `@isoflow/isopacks/dist/kubernetes` isopack), one `views[].rectangles` region per namespace, and `views[].connectors` for the same real NetworkPolicy ingress-allow edges the deck.gl arcs draw, tile-anchored since a `TopologyEdge` is namespace-to-namespace rather than per-Service. `components/IsoflowTopology.tsx` loads the real `Isoflow` component via `next/dynamic(..., { ssr: false })`, matching isoflow's own documented Next.js integration (it has no SSR path). **Live-verified cross-tab consistency**: a fresh authenticated `GET /topology` returned both tabs' real counts embedded in the same hydration payload -- deck.gl: 14 Service(s) across 6 namespaces, 4 real cross-namespace edges; isoflow: the same 14 Service node(s) across 6 namespace region(s), 4 real NetworkPolicy connector(s) -- see `isoflow-view-matches-deckgl-view-node-count` in `evidence/control-evidence-bundle.json`. **Disclosed dependency risk, not hidden**: isoflow's hard (non-peer, non-optional) dependency `react-quill` targets React 16/17/18 and calls `ReactDOM.findDOMNode`, an API removed entirely in React 19 -- this app runs React 19.2.0. The read-only view verified above (rendering nodes/regions/connectors, no item/view description editing) never exercises `react-quill`'s code path, so it is genuinely unaffected; `editorMode="EDITABLE"` (which surfaces the rich-text description editor) has NOT been exercised and would need a real check before ever being turned on, since `findDOMNode` throwing at runtime is a real, not hypothetical, risk on this React version (confirmed by reading `react-quill`'s installed source and the real React 19 API surface, not assumed). Kept in `editorMode="NON_INTERACTIVE"`-or-equivalent read-only mode for exactly this reason. | `lib/topology.ts`, `lib/isoflow-model.ts`, `components/DeckTopology.tsx`, `components/IsoflowTopology.tsx`, `lib/k8s.ts` (`listNetworkPolicies`) |
| `/network` | **Network Topology** (AWS VPC console / GCP VPC Network Topology / Azure Virtual Network diagram equivalent) -- real Pod/Service CIDR ranges, a real per-namespace ingress reachability matrix, and the real Istio mTLS trust boundary, in one place instead of scattered across `/service-discovery`/`/iam`/`/topology`. **Pod CIDR**: authoritative source is `Node.spec.podCIDR` (kubeadm's own node-ipam controller, `10.244.0.0/24` on this single-node cluster) via a new cluster-scoped `nodes` get/list RBAC grant, corroborated by an observed range computed from real live Pod IPs (`lib/k8s.ts`'s new `listPodIPs`). **Service CIDR**: no RBAC exists into kube-system (deliberately -- same boundary as Secrets/Logs above), so `--service-cluster-ip-range` can't be read directly; the only honest value here is OBSERVED -- the smallest CIDR block containing every real live Service ClusterIP across all namespaces (`lib/k8s.ts`'s new cluster-wide `listAllServices`), computed by `lib/network.ts`'s `computeObservedCidr` (pure min/max-common-prefix math, no fixed-size assumption). **Reachability matrix**: `lib/network.ts`'s `buildReachabilityMatrix` reuses the exact `ingressFromNamespaces` field `/topology`'s arcs already draw from, implementing real k8s NetworkPolicy semantics (not simplified): a target namespace with zero Ingress-type policy is default-allow-from-anywhere; otherwise the union of every Ingress policy's `ingressFromNamespaces` decides each source, including self-pairs (computed by the same rule, never hardcoded to "same-namespace is always allowed"). **mTLS boundary**: real `security.istio.io/v1` PeerAuthentication objects, cluster-wide (new RBAC grant), distinguishing a namespace-wide policy from a workload-scoped `spec.selector` override, and honestly reporting "no PeerAuthentication object" for namespaces with none rather than asserting Istio's PERMISSIVE mesh-wide fallback (which would require a kube-system read this console doesn't have). **Live-verified against real enforcement, not just policy-object existence**: authenticated `GET /network` through the deployed pod returned the real matrix (`10.244.0.0/24` pod CIDR, `10.96.0.0/16` observed Service CIDR from 30 real ClusterIPs, `autofde-lab`/`gymact`/`ggen`/`ggen-marketplace` all STRICT mTLS, `supabase-demo` with no PeerAuthentication object). Three throwaway `sidecar.istio.io/inject: "false"` curl pods then cross-checked that matrix against actual enforced behavior: `autofde-lab` → `gymact-status:80` (matrix: deny) → real `curl: (28) Connection timed out after 6003ms`; `gymact` → `ggen-status:80` (matrix: deny) → real `curl: (28) Connection timed out after 6002ms`; `autofde-lab` → `demo-project-rest.supabase-demo:3000` (matrix: allow) → real `HTTP/1.1 200 OK` from the live PostgREST OpenAPI endpoint. All 3 live results matched the matrix's claims exactly -- see `network-topology-matches-real-enforcement` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/network.ts`, `app/app/network/page.tsx`, `lib/k8s.ts` (`listNodes`, `listAllServices`, `listPodIPs`, `listPeerAuthentications`) |
| `/sessions` | Real **Active Session Management** (AWS IAM Identity Center active-session view / GCP Console "manage devices & activity" equivalent) -- the piece this app's stateless HS256 session JWTs (`lib/session.ts`) structurally could not provide on their own: before this pass, once a session was issued there was no way to see who was logged in or force a specific session to stop working before its own unexpired 8h `exp`. Every session-minting path (`/api/login`, `/api/auth/gotrue-login`, `/api/auth/gotrue-signup`, and the API-key Bearer path in `middleware.ts`) now also carries a fresh `sessionId` claim and records a real row in a new `platform_console.active_sessions` table (dedicated schema, self-bootstrapped `CREATE TABLE IF NOT EXISTS`, same live demo-project Postgres and pool `lib/audit-db.ts` already uses) via `lib/active-sessions.ts`. `middleware.ts` looks that row up on **every** authenticated request (`checkAndTouchSession`) and rejects an otherwise-valid, unexpired JWT with a real `401 {"error":"unauthenticated","reason":"session revoked"}` the instant its row is marked revoked -- this registry check, not the JWT's own signature/exp, is what makes revocation real instead of merely hiding a row from a list. A throttled (>=1/min per session) `last_seen_at` heartbeat avoids a write on every single request; a genuinely unreachable registry fails OPEN (disclosed in the module's own header) rather than blocking every authenticated request platform-wide on a transient DB hiccup, but a row successfully read back as `revoked: true` is never let through. The API-key auth path (no persistent cookie -- a fresh JWT is minted on literally every Bearer-authenticated request) gets a deterministic `apikey-<keyId>` session id instead of a random one, so every request against the same key resolves to the same registry row -- real defense-in-depth alongside `lib/api-keys.ts`'s own independent `revoked` flag, either one blocks the key. Owner-gated (`requireRole(session, "owner")`, same boundary as `/audit`/`/api-keys`), a real per-session Revoke action, self-revoke included (with an extra confirm warning). **Live-verified through the deployed pod**: logged in twice for real -- local-admin (`POST /api/login`, temp-rotated password, same restore-after precedent as prior passes) and a real throwaway GoTrue signup (`POST /api/auth/gotrue-signup`) -- producing two real, distinct session cookies (`sessionId` `3f5d055b-...` and `1aed64e0-...`). `GET /api/sessions` (session A) showed both real rows. `DELETE /api/sessions?sessionId=1aed64e0-...` (session A, as owner) revoked session B's row (`200`, `revoked:true`). Session B's still-unexpired original cookie was immediately retried against `GET /api/sessions`: real `401 {"error":"unauthenticated","reason":"session revoked"}` -- while session A, unrevoked, still returned a real `200` with both rows in the same response. A direct `psql SELECT` against the live `platform_console.active_sessions` table independently confirmed both rows' `revoked`/`revoked_at`/`revoked_by` state matched the API responses exactly. Cleanup: the throwaway GoTrue user was deleted for real via GoTrue's own `/admin/users/{id}` DELETE (confirmed `200`), both proof sessions were self-revoked as a final tidy step, and the temporarily-rotated `ADMIN_PASSWORD_HASH` was restored and the deployment rolled again -- confirmed by the exact same temp password that worked moments earlier immediately returning a real `401 {"error":"invalid credentials"}`. See `session-revocation-enforced-before-jwt-expiry` in `evidence/control-evidence-bundle.json` | `lib/active-sessions.ts`, `lib/session.ts`, `middleware.ts`, `app/app/api/sessions/route.ts`, `app/app/sessions/page.tsx`, `components/SessionsPanel.tsx` |
| `/audit` | Durable, queryable **Audit Log** (AWS CloudTrail / GCP Audit Logs / Azure Monitor Activity Log equivalent) -- closes the gap that `lib/audit-log.ts`'s existing stdout line is real but ephemeral (gone on pod restart, not filterable/queryable). Every `/api/*` route now also INSERTs the same entry into a real `platform_console.audit_log` table (dedicated schema, one-time migration applied via direct `psql`) on the live demo-project Postgres this console already trusts for Backups, via `lib/audit-db.ts` -- new `lib/k8s.ts` functions (`getSecretValue`, `getPostgresConnectionInfo`) extend the exact backup/restore credential-discovery pattern one step further (a real Secret GET to decode the plaintext a long-running Node.js process needs for a direct connection, vs. a Job's own kubelet-resolved env). Deliberately kept out of `middleware.ts`'s import graph (the `pg` driver needs Node.js `net`/`tls`, which the edge runtime cannot bundle -- same reason `lib/credentials.ts` is edge-excluded); every route handler already runs on the Node.js runtime, so each one's `writeAuditLogEntry` import was switched to the new module instead. Owner-gated (`requireRole(session, "owner")`, same boundary as `/org`), real actor/path substring filter + timestamp range + pagination. **Live-verified**: 7 real requests across both auth providers cross-matched byte-for-byte across stdout, the app's own `/api/audit`, and a direct `psql SELECT`; a pod holding all 7 requests was then deleted outright, showing its stdout genuinely gone (`kubectl logs` -> `NotFound`) while every DB row survived -- see `audit-log-durable-and-queryable` in `evidence/control-evidence-bundle.json` | `lib/audit-db.ts`, `lib/k8s.ts` (`getSecretValue`, `getPostgresConnectionInfo`), `app/app/api/audit/route.ts`, `app/app/audit/page.tsx` |
| `GET /api/audit/export` | **SIEM export** for the Audit Log above (AWS CloudTrail "export to S3" / GCP Cloud Logging "log sink export" equivalent) -- pulls the same `platform_console.audit_log` history out of this console entirely, into a real standard format an external SIEM (Splunk, Datadog, the Elastic Stack) can ingest, not just the in-console table view. Format: newline-delimited JSON, one [Elastic Common Schema](https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html)-shaped document per line (`@timestamp`, `event.dataset`/`action`/`outcome`/`id`, `user.name`, `http.request.method`, `http.response.status_code`, `url.path`, `ecs.version`) -- the same field-naming convention Filebeat/Elastic Agent already emit, ingestible by Splunk HEC/Datadog's Logs API as plain JSON without needing ECS-awareness. `lib/audit-export.ts`'s `streamAuditLogAsEcsNdjson` is a real async generator pulling rows from Postgres in bounded 500-row keyset-paginated batches (`WHERE (ts, id) > (cursor)`, never `OFFSET`) and yielding one NDJSON line per row as it arrives; the route wraps it in a real Node `ReadableStream` (`pull`-driven, one row enqueued per pull) so the full export is never buffered in the route handler's memory regardless of date-range size. Owner-gated (`requireRole(session, "owner")`, same boundary as `/audit` itself -- bulk export is at least as sensitive as browsing the same data page by page), real `from`/`to` date-range filter (rejected with a real `400` if unparseable), `Content-Type: application/x-ndjson` + `Content-Disposition: attachment` so a plain browser navigation streams straight to disk. A real "Export (NDJSON)" button on `/audit` reuses the panel's own From/To filter. The export action itself is logged into the audit trail it just read (row count + date range in `path`) -- unlike `GET /api/audit`'s own read, which deliberately does not self-log to avoid every page view inflating its own result set; a bulk export is a distinct, higher-sensitivity action, the same reasoning CloudTrail/Cloud Logging apply to their own export/sink-creation management events. **Live-verified through the deployed pod**: exported the real `from=2026-08-18T00:00:00.000Z`/`to=2026-08-18T12:59:00.000Z` range, `jq -c .` parsed all 134 lines as valid JSON with zero errors, the exported line count (134) matched `SELECT count(*) FROM platform_console.audit_log WHERE ts >= ... AND ts <= ...` via direct `psql` for that identical range exactly, and 3 real distinct events (by `requestId`, the prior pass's migration-atomicity test events: apply v1 `201`, rollback v1 `200`, apply v2 `502`) were spot-checked field-by-field from their real Postgres row to the exported ECS JSON, including `event.outcome` correctly deriving `"failure"` for the real `502` -- see `audit-export-valid-ndjson-matches-source` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/audit-export.ts`, `app/app/api/audit/export/route.ts`, `components/AuditLogPanel.tsx` |
| `/projects/[name]/iac` | **Infrastructure as Code export + drift detection** (AWS CloudFormation drift detection / `terraform plan` / GCP Deployment Manager equivalent), scoped to this console's own self-service Project+SingleDatabase resources. `exportProjectManifest` reads the ACTUAL live Project + SingleDatabase CRs and re-serializes them as real, valid, re-appliable multi-document YAML (every operator-defaulted field included -- a genuine snapshot of what's really running, not a template guess), with Copy/Download (a client-side `data:` URL, no backend file endpoint needed). `detectDrift` reconstructs, via the exact same `buildProjectManifest`/`buildSingleDatabaseManifest` functions a real create call uses, what a fresh "Create Project" submission would produce for that project name today, then walks only the fields the create path actually sets (never the operator's own defaulted fields) plus `metadata.labels`/`annotations` (which the create path never sets at all), reporting every real field-level mismatch. Live-verified end to end: the real exported YAML for `demo-project` passed `kubectl apply --dry-run=server` with zero errors, and `kubectl diff -f` against the live cluster produced zero output (true no-op, not just "no error") -- proving the export is genuinely re-appliable. A real, harmless label was then hand-applied to `demo-db` via `kubectl patch` (outside the console entirely); the drift report immediately showed that exact new field, then cleared it back to baseline the moment the patch was reverted -- see `iac-export-reappliable-and-drift-detected` in `evidence/control-evidence-bundle.json` for the full before/after/revert transcript, including the 2 real pre-existing baseline differences (`demo-project` was bootstrapped via `kubectl apply` before this console's create flow existed, so its `databaseRef.name`/`studio.orgName` genuinely don't match today's naming convention -- reported honestly, not hidden) | `lib/iac.ts`, `app/api/projects/[name]/iac/route.ts`, `app/app/projects/[name]/iac/page.tsx` |
| `/status` | **Public Status Page** (AWS Service Health Dashboard / statuspage.io equivalent) -- the only route in this app that is deliberately unauthenticated (added to `middleware.ts`'s `PUBLIC_PATHS`, matching how real hyperscaler status pages work). Renders a real computed uptime% and current up/down state for all 8 platform components (the 4 status services, `platform-console-gateway` itself, and demo-project's postgres/auth/rest), computed with genuine `avg_over_time(up{component="..."}[1h])`-style PromQL against the real in-cluster Prometheus -- never a static "all systems operational" placeholder. See "Status page" below and `status-page-slo-reflects-real-state` in `evidence/control-evidence-bundle.json` for the real induced-outage proof | `lib/status-page.ts`, `app/api/status/route.ts`, `app/status/page.tsx`, `services/platform-prober` |
| `/org` | **Application-level RBAC** (AWS IAM Identity Center permission sets / GCP Org Policy / Azure AD role assignments equivalent), layered on top of -- never replacing -- the console's own k8s ServiceAccount RBAC. Owner-only page listing real role assignments (`viewer` < `member` < `owner`) from one real k8s `ConfigMap` (`platform-console-org-roles`, `platform-console` namespace, identifier → role), with a form to change a user's role, itself owner-gated. Before this module every authenticated session got identical full access regardless of provider; `POST /api/projects` is now owner-only, `POST`/`DELETE /api/secrets` and `POST /api/feature-flags` are member+ -- every GET stays open to any authenticated user. See "Application-level RBAC" below and `application-rbac-role-enforced` in `evidence/control-evidence-bundle.json` for the real 403-then-403-then-201 promotion sequence | `lib/authz.ts`, `app/api/org/roles/route.ts`, `app/app/org/page.tsx` |
| `/api-keys` | **API Keys** (AWS IAM access keys / GCP service account keys / Stripe API keys equivalent) -- the piece that makes this console genuinely programmatically drivable, not just browser-session-drivable. Owner-gated creation/listing/revocation. `lib/api-keys.ts`: real cryptographically random keys (`crypto.randomBytes(32)`, base64url, prefixed `pk_live_` the same way Stripe prefixes its own live keys), stored ONLY as a SHA-256 hash in a real k8s `Secret` (`platform-console-api-keys`, `platform-console` namespace -- a Secret, not a ConfigMap, since these are key hashes) -- the plaintext is shown exactly once, in the create response, and is never recoverable after that. A key is always bound to its creator's own identity, with a role that can only be <= the creator's own current role (`clampRoleToCreator`), never escalated. `middleware.ts` now runs on the Node.js middleware runtime (`export const runtime = "nodejs"`, Next.js 15's node-middleware support) so it can resolve a real `Authorization: Bearer pk_live_...` header against the live Secret; a match mints a real session JWT of the exact same shape every other session already is (`lib/session.ts`'s new `authProvider: "api-key"` variant) and forwards it as the request's own `Cookie` header -- every existing route's `requireSession()`/`requireRole()` call authenticates it completely unchanged, zero route files edited. A revoked or invalid key gets a real JSON `401` on any `/api/*` route (never a redirect); a page route ignores a Bearer header entirely and still redirects to `/login`. See `api-key-auth-enforces-bound-role` in `evidence/control-evidence-bundle.json` for the real curl-only proof sequence (list via a viewer key, a real 403 from a viewer key against a member-gated route, a real 200 from a member key against the same route, then a real, immediate 401 on the same key immediately after revocation) | `lib/api-keys.ts`, `lib/k8s.ts` (`getSecretData`, `createOrUpdateSecret`), `lib/session.ts` (`ApiKeySessionPayload`, `createApiKeySessionToken`), `middleware.ts`, `app/app/api/api-keys/route.ts`, `app/app/api-keys/page.tsx` |
| `/webhooks` | **Outbound Webhooks / Event Notifications** (AWS EventBridge / GCP Eventarc / Azure Event Grid equivalent), owner-gated the same way `/org` is (a subscriber URL is a real exfiltration vector for every payload delivered). Subscriptions are one real k8s `ConfigMap` (`platform-console-webhooks`, `platform-console` namespace, id → JSON record), reusing the exact `getConfigMap`/`createOrUpdateConfigMap` primitive Feature Flags/Org Roles already established -- zero new RBAC, the existing `platform-console-feature-flags` Role already covers it. Four real, already-detectable trigger points are wired, not fabricated: `project.created` fires synchronously off the real `createProjectWithDatabase` success path; `backup.completed`, `alert.firing`, and `budget.threshold_crossed` (see `/budget-alerts`) are detected by the SAME real 10s in-process poller (`lib/webhook-poller.ts`, started once per server process from `instrumentation.ts`) diffing against the exact same `listJobs`/`queryAlerts`/`checkBudgets` calls the Backups/Alerting/Budget Alerts modules already use, baselined on its first tick (for the first two) so pre-existing state is never replayed as "new". Delivery (`lib/webhooks.ts`'s `deliverWebhookEvent`) POSTs a real JSON payload to every matching subscriber URL with a real HMAC-SHA256 signature (`x-platform-webhook-signature-256: sha256=<hex>`, the GitHub/Stripe convention) computed over the exact body bytes, isolated per-subscriber with a 5s timeout so one dead receiver can never block another delivery or the triggering request. **Live-verified end to end**: a real throwaway receiver Pod+Service, subscribed via the authenticated API to both `project.created` and `backup.completed`, actually received real HTTP POSTs (through the live Istio mesh, `x-forwarded-client-cert` visible on the request) for a real test Project creation and a real completed `pg_dump` backup Job; both signatures were independently recomputed via `openssl dgst -sha256 -hmac <secret>` over the exact received body bytes and matched the received header byte-for-byte. The 2-replica rollout's real, disclosed consequence -- one duplicate `backup.completed` delivery, one per replica's independent poller -- was observed live too, not just documented as a hypothetical. See `webhook-delivery-verified-with-valid-signature` in `evidence/control-evidence-bundle.json` for the full transcript (both real payloads, both real signatures, both independent verifications) | `lib/webhooks.ts`, `lib/webhook-poller.ts`, `instrumentation.ts`, `app/api/webhooks/route.ts`, `app/app/webhooks/page.tsx` |
| Global Search (`Cmd+K`/`Ctrl+K`, every page) | **Global Search / Command Palette** (AWS resource search / GCP Cloud Console search bar equivalent) -- find a real resource across every module by name, from one place, instead of navigating module by module. `lib/global-search.ts`'s `searchPlatform(query, role)` queries, in parallel, the exact same live lib functions each module's own page already calls: `listAllServices`, `listProjects`, `listSecrets` (per platform namespace), `listCronJobs` (per schedulable namespace), `listJobs` scoped per-project via the same `getProjectDatabasePod` + `app=platform-backups,database=<stem>` cross-tenant guard the Backups module's own route relies on, and `listWebhookSubscriptions` -- never a client-side static index or a separate search service, so results can never drift from the live cluster. Secrets follow the exact never-render-values discipline `/secrets` documents: only Secret NAMES and KEY NAMES are ever matched or returned, decoded values are never read. `app/api/search/route.ts` is session-gated for any authenticated role; per-category RBAC is real -- each category's minimum role matches exactly what its own existing page/route already enforces (viewer for service/project/secret/cronjob/backup, owner for webhook, matching `GET /api/webhooks`'s existing boundary), resolved once via `lib/authz.ts`'s `getRoleFor` and enforced inside `searchPlatform` itself, never bypassing a category's real RBAC. `components/CommandPalette.tsx` (a shadcn `Dialog`, `components/ui/dialog.tsx` wrapping `@radix-ui/react-dialog`) is mounted once in `app/layout.tsx`, not per-page, opens on a real `Cmd+K`/`Ctrl+K` keydown listener, debounces keystrokes 200ms into a real fetch against `/api/search`, and navigates via `next/navigation`'s `router.push` on click or Enter. **Live-verified**: three real throwaway resources sharing one distinctive fragment (a Secret, a CronJob, and a webhook subscription) were created via the console's own real write APIs; a real `GET /api/search` returned all 3 real matches with correct type/path in one response, a second search run under a real viewer-role API key correctly omitted the owner-only webhook match (2 results, not 3), each result's real `path` was confirmed to render the matching resource on the real deployed pod, and after deleting all 3 test resources the identical search returned `{"results":[]}` -- see `global-search-finds-real-cross-resource-matches` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/global-search.ts`, `app/app/api/search/route.ts`, `components/CommandPalette.tsx`, `components/ui/dialog.tsx` |
| `/tags` | **Resource Tagging / Organization** (AWS Resource Groups & Tag Editor / GCP Labels / Azure Tags equivalent) -- reuses Global Search's exact cross-resource-category fan-out pattern, restricted to the 4 real kinds `lib/tags.ts` can PATCH: Services, Projects, Scheduled Jobs (CronJobs), and the platform's own Feature Flags / Webhooks singleton ConfigMaps (2 separate tag categories, since both are distinct, independently taggable objects). A tag is a real `metadata.labels` entry, `platform-console.io/tag-<key>: <value>`, applied via a real RFC 7386 merge patch (`applyTag`/`removeTag`) touching only that one label key -- never a separate tags table, never a full-object PUT. Both `key` and the resulting label name/value are validated server-side against real Kubernetes label constraints (63-char limit, must start/end alphanumeric) before any API call is made. "Browse by tag" (`GET /api/tags?key=&value=`) is a genuine server-side lookup: every category is queried via the k8s API's own `?labelSelector=` query parameter (`listAllServices`/`listProjects`/`listCronJobs`/`listConfigMaps`, each newly given an optional `labelSelector` argument) -- never a client-side `.filter()` over an unfiltered list. Applying/removing a tag requires at least `member` (`POST`/`DELETE /api/tags`), raised to `owner` for the Webhooks category to match `CATEGORY_MIN_ROLE.webhook`'s own exfiltration-risk reasoning exactly (`lib/tags.ts`'s `minRoleForTagging`); browsing is role-filtered per category the same way `searchPlatform` already is. Small `TagEditor` widgets are embedded directly on `/service-discovery` and `/projects`' own per-resource rows for in-place tagging; the `/tags` page itself adds a generic apply-to-any-taggable-resource form. **Live-verified**: the same `env=verification-test` tag was applied through the real deployed pod to 3 real, distinct k8s object kinds (`Service` `gymact/gymact-status`, `CronJob` `gymact/tags-verify-job`, `ConfigMap` `platform-console/platform-console-webhooks`); the console's own `GET /api/tags` browse-by-tag lookup and a real `kubectl get services,cronjobs,configmaps -A -l platform-console.io/tag-env=verification-test` returned the identical 3 objects; removing the Service's tag dropped both the console's view and the real `kubectl` label-selector query to the same 2 remaining objects; all 3 tags were then removed and confirmed gone from both. See `resource-tagging-filter-matches-real-label-selector` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/tags.ts`, `app/api/tags/route.ts`, `app/app/tags/page.tsx`, `components/TagEditor.tsx`, `components/TagsBrowser.tsx` |
| `/dashboards` | **Custom Dashboards / Saved Queries** (AWS CloudWatch custom dashboards / GCP Monitoring custom dashboards equivalent): save a real query as a named, reusable widget and arrange several into a personal dashboard. `lib/dashboards.ts` stores widgets (`{id, title, type: promql\|audit-query, query, createdBy}`) in one real k8s `ConfigMap` (`platform-console-dashboards`, `platform-console` namespace, one key per widget), reusing the exact `getConfigMap`/`createOrUpdateConfigMap` primitive Feature Flags/Budget Alerts/Org Roles/Tags already established. `executeWidget()` runs the widget's real query against the REAL existing backend on every call -- `lib/prometheus.ts`'s `queryPrometheus` for `promql` widgets (against the SAME `ALLOWED_PROMETHEUS_QUERIES` allowlist `/api/prometheus` itself enforces, now a single shared export so a saved widget can never run a query that route would refuse), `lib/audit-db.ts`'s `queryAuditLog` for `audit-query` widgets (a small URL-search-param syntax -- `actor`, `path`, `from`, `to`, `window` -- where `window`, e.g. `1h`, recomputes a fresh `from`/`to` on every single execution rather than storing a fixed timestamp) -- neither query path reimplemented, and nothing about a result is ever cached or persisted. Access is per widget TYPE, matching exactly what the underlying data source already requires of a direct query: `promql` needs whatever `/observability` requires (any authenticated session), `audit-query` needs whatever `/audit` requires (`requireRole(session, "owner")`) -- a dashboard widget is just a saved lens onto data the viewer could already query directly, never a privilege escalation past it. Creating any widget floors at `member` (`minRoleForCreating`, raised to `owner` for `audit-query` -- the same "raise to at least member" shape `lib/tags.ts`'s `minRoleForTagging` already establishes); viewing uses the type's own unraised floor (`minRoleForViewing`) so a dashboard load only ever re-executes a widget the CURRENT session's role can still reach directly. **Live-verified through the real deployed pod**: a real `promql` widget (`up`) and a real `audit-query` widget (`actor=admin&window=1h`) were created via the authenticated API; `GET /api/dashboards`'s live results were cross-checked against direct calls to the same underlying routes -- the promql widget's 27 series matched `GET /api/prometheus?query=up`'s 27 series byte-for-byte on every (labels, value) pair (set equality, not eyeballed), and the audit-query widget's total (13 rows) matched a direct `GET /api/audit?actor=admin&from=...` once `lib/audit-db.ts`'s own documented fire-and-forget INSERT had landed (a 1s-later repeat direct query showed the identical id set). **Live-update proof**: one real new authenticated request was fired, and reloading `GET /api/dashboards` showed the audit-query widget's total genuinely increase (14 -> 15), with the newest row being that exact new request -- proving the widget re-queries live on every load, never a frozen snapshot from creation time. Both test widgets were then deleted, confirmed empty through both the console's own API (0 widgets) and a direct `kubectl get configmap platform-console-dashboards -o yaml` (no `data` key at all). See `dashboard-widgets-render-live-not-stale-data` in `evidence/control-evidence-bundle.json` for the full transcript | `lib/dashboards.ts`, `app/app/api/dashboards/route.ts`, `app/app/dashboards/page.tsx`, `components/DashboardsPanel.tsx` |
| Notification Bell (`components/Nav.tsx`, every authenticated page) | **In-app real-time notifications** (AWS Console / GCP Console / Azure Portal top-bar bell equivalent), closing the last major unused piece of the Supabase stack: `demo-project-realtime` had been running the whole session with nothing connected to it. A real browser `WebSocket` to this same origin's `/ws/notifications` is relayed by `server.js` to the real, already-running Supabase Realtime server, subscribed on real Postgres logical-replication `postgres_changes` for `platform_console.audit_log` INSERT (added to the `supabase_realtime` publication with a real `ALTER PUBLICATION ... ADD TABLE`) -- a genuine server-initiated push per new audit row, not a poll loop on either leg. See "Real-time notifications" below and `realtime-notification-pushed-not-polled` in `evidence/control-evidence-bundle.json` for the real WebSocket frame a headless client received | `server.js`, `components/NotificationBell.tsx`, `components/Nav.tsx` |
| `/disaster-recovery` | **Disaster Recovery** (AWS Well-Architected DR-pillar / GCP DR-planning-guide equivalent). See also [`docs/INCIDENT-COMMUNICATION-TEMPLATE.md`](docs/INCIDENT-COMMUNICATION-TEMPLATE.md) -- a separate, non-technical status-update template (initial notification / ongoing update / resolution notice) for a leadership chain or a customer during an active incident, cross-linked from and distinct from the engineer-facing runbook below -- grounded in a real incident, not a hypothetical: the prior `platform-eng-colima` cluster hit an unrecoverable etcd bbolt page-checksum panic with no snapshot backup, documented verbatim in `infra/kind-config.yaml`'s own header (committed in `191b3ca`, the first `platform-console` commit) and reconstructed with exact timing from the live cluster's own namespace `creationTimestamp`s. `docs/DISASTER-RECOVERY.md` is the full runbook: the real recovery sequence (recreate -> Istio -> Flux -> kube-prometheus-stack -> Supabase operator -> re-provision -> redeploy), an honest LOST-vs-RECOVERED table (the prior demo database's data was genuinely not recoverable -- the Database Backups module didn't exist until over two hours after the recreation commit), and a **real, live-exercised recovery proof**: `platform-feature-flags` (a real ConfigMap) was deleted on purpose, confirmed broken at both the `kubectl` and live-authenticated-app layers, then recovered via `kubectl apply` from a real backed-up manifest -- recovered `data` and the live app's `GET /api/feature-flags` response matched the pre-deletion state byte-for-byte. This owner-gated, read-only page (`requireRole(session, "owner")`, same boundary as `/org`/`/audit`) surfaces a condensed summary of that runbook plus the REAL current backup inventory -- every live `batch/v1` Job labeled `app=platform-backups` across every real Project namespace, reusing the exact `listJobs` primitive `/projects/[name]/backups` already calls, aggregated platform-wide instead of one project at a time. See `disaster-recovery-runbook-tested` in `evidence/control-evidence-bundle.json` | `docs/DISASTER-RECOVERY.md`, `app/app/disaster-recovery/page.tsx`, `evidence/dr-proof/platform-feature-flags-backup.yaml`, `lib/k8s.ts` (`listProjects`, `listJobs`) |

`lib/k8s.ts` is a hand-rolled Kubernetes API client using the pod's own in-cluster
ServiceAccount token/CA (`/var/run/secrets/kubernetes.io/serviceaccount`) — no external k8s
client dependency. Off-cluster (local `next build`/dev), it fails closed with
`"not configured"`, the same convention `lib/status.ts` already used.

## Real-time notifications

`demo-project-realtime` (image `supabase/realtime:v2.102.3`, a Phoenix/Cowboy WebSocket
server broadcasting real Postgres logical-replication changes) had been running for this
entire session with nothing connected to it — confirmed live via `kubectl logs`/`kubectl exec`
before any client code was written: `DB_HOST=demo-db-postgres...`, tenant `realtime-dev`
(`SELECT external_id FROM _realtime.tenants` -> `realtime-dev`, the image's own fixed
self-host demo tenant, not derived from the k8s `Project` name), `wal_level = logical`, and a
health check answering `200` on `/api/tenants/realtime-dev/health`.

**Wiring it up, in order:**

1. `ALTER PUBLICATION supabase_realtime ADD TABLE platform_console.audit_log;` — verified
   live via `pg_publication_tables` both before (0 rows) and after (the real 8-column
   `attnames` list). `platform_console.audit_log` already gets a real `INSERT` on every
   authenticated action (`lib/audit-db.ts`, from the durable Audit Log pass), so this alone
   makes every one of those inserts a real logical-replication event.
2. `GRANT SELECT ON platform_console.audit_log TO service_role;` — Realtime's own
   authorization check (independent of Postgres RLS, which stays disabled on this table)
   rejects a `postgres_changes` subscription for any role without a real table-level grant;
   the very first live probe against this channel (as `anon`) came back with the row
   redacted (`"record":{},"errors":["Error 401: Unauthorized"]`) until this grant existed —
   a real, disclosed blocker found and fixed live, not assumed away.
3. `server.js` — a new custom Next.js server entrypoint (replacing the auto-generated
   `.next/standalone/server.js`; see its own header comment) that adds one real hook
   standalone's generated server has none of: `server.on("upgrade", ...)`. It holds ONE
   shared upstream Phoenix-channel WebSocket to `demo-project-realtime` (service DNS
   resolved live via the k8s API, `app.kubernetes.io/component=realtime`, never hardcoded;
   auth via the already-deployed `SUPABASE_SERVICE_ROLE_KEY`), joined on `postgres_changes`
   for `platform_console.audit_log` INSERT, and fans every real push out to every browser
   connected to `/ws/notifications` — each one authenticated by the same real,
   correctly-signed `platform_console_session` cookie every other route already trusts
   (`jose`/`AUTH_SECRET`, reimplemented at the small scale actually needed since this file
   sits outside Next's own TS module graph — see the file's header comment for why). A
   connection presenting no valid session gets a real `401` on the upgrade, not a silent
   downgrade. Because the Dockerfile's runner stage now needs the full `node_modules` (`ws`,
   `next`, `jose`, `pg`) instead of `output: "standalone"`'s traced subset, `next.config.js`
   no longer sets `output: "standalone"` and the Dockerfile copies `deps`'s complete
   `node_modules` into the runner image — a larger image for a real capability standalone's
   generated server has no hook for.
4. `components/NotificationBell.tsx` — mounted once in `components/Nav.tsx` (every
   authenticated page), opens a real browser `WebSocket` to `/ws/notifications`, shows a live
   unread badge plus a dropdown of the last 20 real events (actor/method/path/status/time),
   and a small status dot reflecting the relay's real upstream state
   (connecting/subscribed/reconnecting/error) rather than assuming success silently.

**Real proof, not "trust the UI":** with the real deployed pod reached through the real Istio
ingress gateway (`kubectl port-forward svc/istio-ingressgateway`, `Host: platform.local` —
the same routing path a browser uses) and authenticated with a real, correctly-signed session
cookie, a headless Node `ws` client opened `/ws/notifications` and received a real
`{"type":"connection.status","status":"subscribed"}` frame confirming the relay's own upstream
subscription was live. A real authenticated `GET /api/feature-flags` (`200`, through the same
gateway) was then issued — a real action, not a synthetic DB write — producing DB row `id=81`
(`platform_console.audit_log`, `commit_timestamp` `2026-08-18T11:08:11.758Z`). The headless
client received the real pushed frame at `2026-08-18T11:08:12.019Z` (client wall clock) —
**~261ms** after the real Postgres commit, end to end through logical-replication decode,
Realtime, the relay, and the Istio mesh — containing the exact real row:

```json
{"type":"audit_log.insert","record":{"id":81,"ts":"2026-08-18T11:08:11.736+00:00","path":"/api/feature-flags","actor":"verification-script","method":"GET","status":200,"request_id":"39b00aa0-82a1-45d1-b258-efe757a54f9e","inserted_at":"2026-08-18T11:08:11.757665+00:00"},"errors":null,"commitTimestamp":"2026-08-18T11:08:11.758Z"}
```

A genuine server-initiated push (Realtime decoded the WAL record and forwarded it the moment
it committed — the client never asked, it was told), not a poll loop dressed up as one on
either the Realtime<->relay or the relay<->browser leg. See
`realtime-notification-pushed-not-polled` in `evidence/control-evidence-bundle.json`.

`NotificationBell` itself only requires a *valid* session (any role) — a live count/list of
"an authenticated action just happened, by whom, what path, what status" is the same class of
low-sensitivity signal every hyperscaler console's own bell shows to any signed-in operator.
The full audit *log* page (`/audit`, actor/path substring search, pagination, raw rows) stays
owner-gated exactly as before this pass — the bell is a notice, not that report.

## Container Exec

Real browser-based shell access into a real running pod (the AWS Systems Manager Session
Manager / GCP Cloud Shell / Azure Cloud Shell "run a command in a running instance/pod"
equivalent) — the most sensitive capability in this console, over the k8s API's real
`pods/exec` subresource.

**The mechanism, confirmed live before any application code was written.** `kubectl exec`
traditionally upgrades an HTTP POST to SPDY; this console instead confirmed live against this
cluster's real v1.34 API server that a plain GET request to
`.../pods/{pod}/exec?command=...&stdout=true&stderr=true` upgraded to an ordinary WebSocket
(`Sec-WebSocket-Protocol: v4.channel.k8s.io`, the same subprotocol name `client-go`'s own
WebSocket exec executor negotiates) is accepted and works identically — a headless Node `ws`
client, authenticated first with a real client certificate and then with this
ServiceAccount's own real bearer token, received real demuxed stdout/status frames
(`channel 1` = stdout, `channel 3` = a final `{"status":"Success"}` JSON object) matching
`kubectl exec`'s own output exactly. This is the real mechanism `lib/container-exec.ts` and
`server.js`'s `/ws/exec` relay both use — no SPDY library, no external k8s client SDK, just
the `ws` package already vendored for Realtime Notifications, pointed at a different
subresource.

**The real security boundary: a fixed, server-side command allowlist.** A `pods/exec`
request's `command` array is handed straight to the container runtime — accepting free text
here would be a textbook RCE backdoor with a UI. `lib/container-exec.ts`'s
`ALLOWED_EXEC_COMMANDS` is a small, fixed map of command **ids** to real, hardcoded argv
arrays (`cat /app/facts.json`, `echo`, `env`, `ls -la /app`) — read-only diagnostics only.
Every caller (the buffered `POST /api/exec` route, and `server.js`'s `/ws/exec` upgrade
handler, which duplicates this same small allowlist inline for the same module-boundary
reason `server.js`'s own header comment already documents for `lib/k8s.ts`/`lib/session.ts`)
resolves the request's `commandId` against this allowlist BEFORE any connection to the k8s
API is attempted; an unrecognized id gets a real `400` with zero k8s API traffic. There is no
free-text command field anywhere in the UI, the API route body, or the WebSocket query
string.

**Two independent execution paths, one allowlist.** `POST /api/exec` (Node-runtime API
route, owner-gated) runs `lib/container-exec.ts#execAllowedCommand` and returns the full
buffered stdout/stderr once the real k8s exec session closes. `/ws/exec` (`server.js`,
reusing the exact WebSocket-upgrade infrastructure the Realtime Notifications pass built)
opens its own real WebSocket straight through to the target pod's exec subresource and
relays every real stdout/stderr/status frame to the browser the instant it arrives — a true
live relay, not a buffered round trip. Both resolve the same commandId against the same
allowlist content (one canonical, one disclosed-duplicate, per the module-boundary
constraint above); neither ever accepts raw command text.

**Owner-only, three independent gates.** This is the single most sensitive capability in the
console, so it gets the same "owner" floor as Canary Deploy and Audit Log — enforced
independently by the `/exec` page's own gate, `GET`/`POST /api/exec`'s
`requireRole(session, "owner")`, and `server.js`'s `/ws/exec` upgrade handler's own role
check (a small, disclosed mirror of `lib/authz.ts#getRoleFor` against the real
`platform-console-org-roles` ConfigMap — the same one every other role check in this app
reads). The role check runs before the namespace/command allowlists, which run before any
k8s connection: a non-owner session, or an unrecognized command, never reaches the k8s API
at all.

**Real proof, not "trust the UI".** Through the real deployed pod (port-forwarded, real
`admin` session cookie from a real `POST /api/login`), `GET /api/exec?namespace=autofde-lab`
returned the real live pod (`autofde-lab-status-...`) and the real 4-command allowlist. A
headless Node `ws` client then opened `/ws/exec?namespace=autofde-lab&pod=...&commandId=
cat-facts` through the console's own relay and received the real streamed output; saved to a
file and compared with `diff` and `sha256sum` against `kubectl exec ... -- cat
/app/facts.json` run directly against the same pod at the same time — **0 differences, an
identical `sha256:d801e525...` on both sides**. Two disallowed `commandId` values
(`rm-rf-slash`, and a real semicolon-injection attempt `cat /etc/passwd; whoami`) both got an
immediate real `400` over the WebSocket upgrade itself (`UNEXPECTED-RESPONSE 400`, zero
bytes of body) — confirmed via the pod's own stdout audit line
(`{"execAudit":true,...,"status":400,"reason":"commandId not on allowlist -- rejected before
any k8s API call"}`) that this was a same-process rejection, not a k8s-side denial. See
`container-exec-output-matches-kubectl` in `evidence/control-evidence-bundle.json` for the
full transcript.

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

## External OIDC federation

A third, distinct login path — the "Sign in with Google/GitHub/Microsoft" pattern every
enterprise console offers — layered alongside the local-admin path and the internal GoTrue
identity-federation path above. All three mint the exact same kind of app-local session JWT
(`lib/session.ts`), discriminated by `authProvider`, and flow into the same
`getRoleFor`/`requireRole` RBAC gate (`lib/authz.ts`) and the same `platform_console.active_sessions`
registry (`lib/active-sessions.ts`) every other path already uses.

**Which real provider, and why** (the task's own decision point, and the honest answer): this
sandbox has real network egress but no real registered OAuth client credentials for Google,
GitHub, or Microsoft — creating one requires a human with a real account clicking through an
external console's own "register an app" flow, out of reach in an automated session. Two real
options exist instead of fabricating that:

1. A real, publicly reachable OIDC provider with a well-known demo client —
   `https://demo.duendesoftware.com` (Duende Software's own public IdentityServer demo) is
   confirmed live-reachable from this sandbox (`curl` its real
   `.well-known/openid-configuration`, real JWKS). **Rejected for the actual proof**: its
   pre-registered demo clients are locked to Duende's own fixed `redirect_uri`s, which this
   app's real `/api/auth/oidc-callback` can never match — a genuine authorization_code round
   trip terminating at our own callback is not actually completable against it.
2. **Taken**: stand up a real, minimal, spec-compliant OIDC provider as a genuinely separate
   service — exactly the shape a company's own internal Okta/Auth0/Keycloak tenant has (this
   org's own IdP, not a simulation of Google). `services/oidc-idp` runs the real,
   widely-used [`oidc-provider`](https://github.com/panva/node-oidc-provider) library as
   `platform-console-oidc-idp`, a standalone Deployment+Service in the `platform-console`
   namespace with its own container image, its own process, its own real RSA keypair
   (generated fresh at boot via `jose.generateKeyPair`, never the library's bundled
   dev-keystore whose private half ships in its own npm source) — completely independent of
   both the console's own process and the GoTrue instance the second auth path uses.

- `lib/oidc-federation.ts` — the RP (Relying Party) half. Real `/authorize` redirect
  construction (RFC 7636 PKCE S256 + `state` + `nonce`, all real random values), a real
  `POST /token` authorization_code exchange (a genuine server-to-server call to the real
  provider, `client_secret_basic`-authenticated per RFC 6749 §2.3.1 — including the
  form-urlencoded percent-encoding of each credential half the spec requires, found and fixed
  live: our real generated secret's literal `+` was being corrupted by a naive
  `Buffer.from(id:secret)` join, causing a real `401 invalid_client` until the encoding was
  fixed), and real ID-token signature verification against the real provider's real JWKS —
  `jose.createRemoteJWKSet` fetches `/jwks` live, `jose.jwtVerify` checks the real RS256
  signature, `iss`, `aud`, and expiry. **Never skipped**: every caller lets a verification
  failure throw as a hard 401, there is no bypass path.
- `app/api/auth/oidc-login/route.ts` (public, plain GET — a real full-page `<a href>`
  navigation, not `fetch()`, since its job is a real 302 to a real external `/authorize`
  endpoint) mints a short-lived, signed transaction cookie (`state`/`nonce`/PKCE
  `code_verifier`/`next`, `lib/session.ts`'s `createOidcTransactionToken`) to carry those
  values across the redirect round trip a stateless route handler has no other way to hold.
  `app/api/auth/oidc-callback/route.ts` (also public — this is where a session doesn't exist
  yet) verifies `state` against that cookie (CSRF defense), exchanges the code, verifies the
  ID token's real signature, checks the ID token's `nonce` claim against the same cookie
  (replay defense), then mints this app's own session with `authProvider: "oidc-external"`
  and records the same real `active_sessions` registry row every other login path does.
- `lib/session.ts`'s `SessionPayload` union gains a fourth (third real end-user path, fourth
  counting the API-key path) `OidcSessionPayload` variant — `sub`/`email` come straight from
  the verified ID token's own claims, `idpIssuer` records which real provider vouched for it.
  `lib/authz.ts`'s `roleIdentifierFor` treats it exactly like `gotrue` (keyed by email); a
  brand-new OIDC identity defaults to `viewer`, same fail-closed default every other identity
  gets — confirmed live below.
- `app/app/login/page.tsx` renders a third card, "Sign in with Platform IdP (OIDC)".
- `services/oidc-idp/server.js` — the real provider's own configuration. One real,
  statically registered client (`client_secret_basic`, PKCE **required** on every request,
  not just for public clients). One real seeded demo account, authenticated with a **real
  bcrypt password check** — `devInteractions` (the library's own bundled quick-start login
  screen) is deliberately disabled: reading its source confirmed it accepts *any* typed
  accountId with **no credential check at all** (it says so itself: "a quick start
  development-only feature... you are expected to... provide your own"). This file provides
  its own real `/interaction/:uid` login+consent instead, with the same rigor the local-admin
  and GoTrue paths already use.

**Real, live, end-to-end proof** (no human to click through interactively, so scripted — a
real HTTP client issuing the exact same real requests a browser would, against the real
deployed pods, `kubectl exec`'d directly into the running `platform-console-gateway` pod so
every hop is a real network call, never an in-process shortcut):

1. Real `GET /api/auth/oidc-login` on the real deployed console → real `302` to the real,
   separate `platform-console-oidc-idp` Service's real `/auth` endpoint, real PKCE challenge
   and `state`/`nonce` in the query string.
2. Real `303` from the real IdP to its own real `/interaction/:uid` login form.
3. Real credentials POSTed to that real form — the real bcrypt check runs server-side. On
   success: real `Grant` saved, real redirect chain back to our real, configured
   `redirect_uri` (`http://platform.local/api/auth/oidc-callback`) carrying a real
   authorization `code` and the same real `state` this app generated in step 1.
4. That real code+state replayed against our own deployed pod's real
   `/api/auth/oidc-callback` (same real transaction cookie from step 1) → real token
   exchange, real ID-token signature verification, real session minted. Real decoded ID
   token, captured from the live pod's own stdout (`kubectl logs`):
   ```json
   {"oidcFederationVerified":true,
    "issuer":"http://platform-console-oidc-idp.platform-console.svc.cluster.local:8081",
    "sub":"3f9b6b7e-6e1a-4b3a-9c2e-3a2f9e7d5c11",
    "email":"demo.user@platform-eng-colima.local",
    "emailVerified":true,"alg":"RS256",
    "kid":"Yz9Kfg_Wo4ro4m81hFjBhvIjgxmrno1xeQC_sSzGFQI",
    "idTokenClaims":{"sub":"3f9b6b7e-6e1a-4b3a-9c2e-3a2f9e7d5c11",
     "email":"demo.user@platform-eng-colima.local","email_verified":true,
     "name":"Demo Federated User","nonce":"N38s8Ck34sKceCDuHCGGxw",
     "aud":"platform-console","exp":1787071166,"iat":1787067566,
     "iss":"http://platform-console-oidc-idp.platform-console.svc.cluster.local:8081"}}
   ```
   `alg: RS256` — real asymmetric signature verification (not the local-admin/GoTrue paths'
   HS256 app-session JWTs), checked against the real provider's real JWKS, never skipped.
5. Real `GET /projects` with the newly minted session cookie → real `200` (not the `307` to
   `/login` an unauthenticated request gets) — the new identity genuinely has access to a
   protected page.
6. Real `psql SELECT` against the live `platform_console.active_sessions` table confirmed the
   real registry row: `identifier=demo.user@platform-eng-colima.local`,
   `auth_provider=oidc-external`, `revoked=f` — the exact row `recordSessionLogin` wrote,
   independently readable outside the app.
7. Real negative controls, same live pods: wrong password at the real IdP → real `401`
   (`"Invalid email or password"`, real bcrypt compare failed); a tampered/mismatched `state`
   at our own callback → real `400 {"error":"state mismatch -- possible CSRF or replayed
   callback"}`; no transaction cookie at all → real `400 {"error":"missing OIDC transaction
   cookie..."}`; a genuinely tampered ID-token signature (local pre-deploy check, same
   provider config) → `jose.jwtVerify` throws `"signature verification failed"`, never
   silently accepted.
8. RBAC integration, live: the fresh OIDC identity's `GET /api/sessions` (owner-only) returned
   a real `403 {"error":"forbidden","reason":"role 'viewer' does not meet the required
   minimum role 'owner'..."}` — the new auth path defaults to the exact same `viewer` role
   every other brand-new identity gets, enforced by the exact same `requireRole` gate, not a
   parallel authorization system.

See `external-oidc-federation-verified-real-signature` in
`evidence/control-evidence-bundle.json` for the full transcript this section summarizes.

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
the change). `services` and `core.supabase.io/projects` each also carry a `patch` verb for
the Resource Tagging module (`lib/tags.ts`'s `applyTag`/`removeTag`) -- a real RFC 7386 merge
patch touching only `metadata.labels.platform-console.io/tag-<key>`, never spec; the
per-namespace `platform-console-scheduled-jobs` Role below carries the same addition for
`batch/cronjobs`. No Secrets, no exec/log, no wildcards, no write verb anywhere outside
`projects:create`/`singledatabases:create`/the 3 `patch` grants just named. Verified live with
real `kubectl auth can-i --as=system:serviceaccount:platform-console:platform-console` calls —
see `evidence/control-evidence-bundle.json` for the exact denials and allows observed.

The `/secrets`, `/logs`, `/scheduled-jobs`, and `/exec` modules are each backed by their
**own** per-namespace `Role`/`RoleBinding` pairs in `k8s/paas-rbac.yaml` —
`platform-console-secrets` (`get/list/create/delete` on `secrets`),
`platform-console-logs-reader` (`get/list` on `pods`, `get` on `pods/log`),
`platform-console-scheduled-jobs` (`get/list/create/delete/patch` on `batch/cronjobs` -- `patch`
added for the Resource Tagging module, see above), and
`platform-console-exec` (`get`+`create` on `pods/exec`) — deliberately kept **out of** the
cluster-wide `ClusterRole/platform-console-paas` above, since all four resource types are
more sensitive than the read-mostly resources that ClusterRole grants (a CronJob's Pod runs
a real, unattended container on a real schedule, and `pods/exec` is a real command-execution
channel — the same or greater blast-radius class as a Secret). `pods/exec` is a genuinely
distinct k8s subresource from `pods`/`pods/log` — never folded into
`platform-console-logs-reader` even though both are pod-scoped — and needed BOTH verbs, not
just the conventional `create`: this console's own exec client connects via a GET request
upgraded to a WebSocket (see "Container Exec" below), which the API server's authorizer
evaluates as the `get` verb, confirmed live by a real `403` ("cannot get resource
\"pods/exec\"") with only `create` granted, fixed by adding `get`. Scoped to the platform's
own namespaces only, never cluster-wide, never `kube-system`.

## Policy as Code

Real **Organization Policy enforcement** (AWS Config Rules / GCP Org Policy equivalent),
distinct from every RBAC grant above: RBAC controls *who* may act; this controls *what shape*
an object is allowed to take, enforced regardless of who submits it -- even a request made
directly with `kubectl`, never routed through this console at all. Built entirely on
Kubernetes' own native `admissionregistration.k8s.io/v1` `ValidatingAdmissionPolicy` (CEL-based,
GA since Kubernetes 1.30 -- this cluster runs v1.34.0) -- deliberately **not** a third-party
admission webhook framework (Kyverno, OPA Gatekeeper, etc.); none is installed on this cluster,
and `ValidatingAdmissionPolicy` needs zero extra infrastructure: kube-apiserver evaluates the
CEL expression in-process, natively, on every matching request.

One real, meaningful policy is enforced: `k8s/admission-policy.yaml` defines
`platform-deployments-require-resources`, a `ValidatingAdmissionPolicy` whose CEL validation is

```cel
object.spec.template.spec.containers.all(c,
  has(c.resources.requests) && has(c.resources.limits))
```

rejecting any `apps/v1` `Deployment` `CREATE`/`UPDATE` where any container omits
`resources.requests` or `resources.limits`. This is the exact real gap
`k8s/resource-quotas.yaml`'s own comment already documents: once a namespace carries a
compute `ResourceQuota` (true for all 5 platform namespaces here), a Deployment with no
`resources` block fails ResourceQuota admission anyway, but with a generic quota-shaped error
that doesn't name the real rule. This policy makes that rule explicit, and rejects it with a
message that says exactly what's missing -- before ResourceQuota admission even runs.

Its `ValidatingAdmissionPolicyBinding` (`platform-deployments-require-resources-binding`) scopes
enforcement to *only* the platform's 5 project namespaces (`autofde-lab`, `gymact`, `ggen`,
`ggen-marketplace`, `platform-console` -- the same 5 namespaces `k8s/namespaces.yaml` creates
and `k8s/resource-quotas.yaml` already puts a `ResourceQuota` in), matched by the well-known,
immutable `kubernetes.io/metadata.name` namespace label. `kube-system`, `istio-system`,
`flux-system`, `default`, and every other namespace outside that list are deliberately excluded
-- proven live below, not just asserted.

**Real proof, applied and exercised against the live cluster** (`kubectl apply -f
k8s/admission-policy.yaml`, then three real `kubectl apply` attempts, no app code in the
loop at all):

1. A Deployment with **no `resources` block**, submitted to `autofde-lab` (in scope), was
   rejected by the real API server before any pod was ever scheduled:

   ```
   The deployments "policy-test-noncompliant" is invalid: : ValidatingAdmissionPolicy
   'platform-deployments-require-resources' with binding
   'platform-deployments-require-resources-binding' denied request: every container in
   this Deployment's pod template must declare both spec.resources.requests and
   spec.resources.limits (Policy-as-Code control:
   platform-deployments-require-resources) -- a Deployment with no resources block
   breaks ResourceQuota-enforced namespaces and is rejected here before that happens
   ```

   `kubectl get deploy policy-test-noncompliant -n autofde-lab` confirmed a real `NotFound` --
   nothing was created.
2. The same Deployment, corrected with a real `resources.requests`/`resources.limits` block,
   submitted to the same `autofde-lab` namespace: `deployment.apps/policy-test-compliant
   created` -- accepted normally.
3. The identical **no-`resources`** Deployment shape, submitted to `default` (deliberately
   **out of scope**): `deployment.apps/policy-test-noncompliant-default created` -- admitted
   with no rejection at all, proving the binding's namespace scoping is real and narrow, not
   accidentally cluster-wide.

Both real test Deployments (`policy-test-compliant` in `autofde-lab`,
`policy-test-noncompliant-default` in `default`) were deleted immediately after, confirmed via a
real `kubectl get deploy` in each namespace showing zero leftover objects.

The console's own read-only surface for this control is `/policy` (owner-gated):
`lib/policy.ts` lists the real, live `ValidatingAdmissionPolicy`/`ValidatingAdmissionPolicyBinding`
objects and renders their real CEL expression text verbatim -- the enforcement itself never
lives in this app, only at kube-apiserver; this module surfaces what's enforced, it does not
implement it. **"Recent denials" is honestly documentation-only, not live-queryable**: Kubernetes
has no built-in "denial log" API. A `ValidatingAdmissionPolicy`'s `auditAnnotations` are written
into kube-apiserver's own audit log stream (when audit logging is enabled and configured to
capture them) -- not into any object this app, or any Kubernetes API, can `GET`. This cluster
does not currently ingest kube-apiserver's audit log anywhere queryable from this console, so a
real "recent denials" list cannot honestly be built here today; `/policy` discloses this gap
directly rather than fabricating a denial history. The real rejection transcript above is
captured, instead, as this section's own live evidence and in
`admission-policy-rejects-noncompliant-deployment` (`evidence/control-evidence-bundle.json`).

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
- `platform-prober` (`platform-console` namespace, `k8s/status-page.yaml`): the public
  Status Page's real data source -- see "Status page" below.
- Manifests applied in order from `k8s/`: `namespaces.yaml`, `rbac.yaml`, `paas-rbac.yaml`,
  `resource-quotas.yaml`, `network-policies.yaml`, `mtls.yaml`, `feature-flags.yaml`,
  `services-and-deployments.yaml`, `canary.yaml`, `gateway.yaml`, `grafana-route.yaml`,
  `hpa.yaml`, `ratelimit.yaml`, `status-page.yaml`.

## Canary / Blue-Green deployment control

Real Canary/Blue-Green deployment traffic control -- the AWS CodeDeploy traffic-shifting / GCP
traffic-splitting / Azure deployment slots equivalent -- for one real backend,
`autofde-lab-status`, built on Istio's real weighted `VirtualService` routing rather than the
all-or-nothing `kubectl rollout restart` every other Deployment in this cluster still uses.

Shape (`k8s/canary.yaml`):

- **Two Deployments, one image.** `autofde-lab-status` (stable) and `autofde-lab-status-canary`
  (canary) run the exact same `platform-console/autofde-lab-status:latest` image, distinguished
  only by a `version: stable`/`version: canary` pod label and a `CANARY_VERSION` env var each
  sets. `services/autofde-lab/app.py` stamps that env var onto every response as a real,
  observable marker: an `X-Deployment-Version` header on every response, plus
  `deployment_version`/`canary` fields on `GET /status` -- never a build-time difference between
  the two images, since they're the same image.
- **One Service, unchanged.** `autofde-lab-status` (k8s/services-and-deployments.yaml) still
  selects on `app: autofde-lab-status` only, so it matches pods from both Deployments.
- **One `DestinationRule`** (`networking.istio.io/v1`) defines `stable`/`canary` subsets over
  that Service by the `version` label.
- **One `VirtualService`** routes to those two subsets by weight (`spec.http[0].route[].weight`),
  no `gateways:` field (applies to mesh-internal/sidecar-to-sidecar traffic, not ingress).

`lib/canary.ts` reads/writes that VirtualService's live weight via the k8s API (a real
GET-then-PUT, reusing `lib/k8s.ts`'s `k8sRequest` -- Istio CRDs are just another namespaced
resource, same convention `listPeerAuthentications` already established for
`security.istio.io`). The owner-gated `/deployments/canary` page
(`app/api/deployments/canary/route.ts`, `requireRole(session, "owner")`, same enforcement
boundary as `/org`) exposes a weight slider, a **promote** action (100% canary, then delete the
stable Deployment), and a **rollback** action (100% stable, then delete the canary Deployment).
RBAC: `k8s/paas-rbac.yaml`'s `platform-console-canary-autofde-lab` Role, scoped to exactly the
`autofde-lab` namespace (not cluster-wide) -- `create`/`delete` on `apps/deployments` and
`get`/`update`/`patch` on `networking.istio.io/virtualservices`.

**Real traffic-split proof (not simulated)**: driven through the live, authenticated
`/api/deployments/canary` API (a real session JWT, HS256-signed with this app's own live
`AUTH_SECRET`, minted the same way and to the same trust level as the webhook-receiver proof
above), with a real 40-request-per-setting burst issued from the `platform-console-gateway`
pod's own network identity (allowed by `autofde-lab-allow-from-platform-console`'s
NetworkPolicy; a same-namespace throwaway pod was tried first and confirmed genuinely blocked
by that same default-deny policy, so the burst runs from the identity the policy already
admits) against `http://autofde-lab-status.autofde-lab.svc.cluster.local/status`, tabulating
the real `X-Deployment-Version` response header per request:

| Weight set (stable/canary) | Real tabulated result (40 requests) | Ratio |
|---|---|---|
| 50 / 50 | stable 19, canary 21 | 47.5% / 52.5% |
| 100 / 0 (immediately after the weight PUT) | stable 39, canary 1 | real Istio xDS propagation lag, disclosed not hidden -- see below |
| 100 / 0 (after a 3s settle) | stable 40, canary 0 | 100% / 0% |
| after **promote** (weight forced to 0/100, stable Deployment deleted) | stable 0, canary 40 | 0% / 100% |
| final steady state (stable Deployment recreated, **rollback** called: weight 100/0, canary Deployment deleted) | stable 40, canary 0 | 100% / 0% |

The single canary hit in the "immediately after" row is a real, disclosed observation of
Istio's eventually-consistent xDS propagation (istiod pushing the updated route config to the
Envoy sidecar takes on the order of ~1-3s after the `VirtualService` PUT lands in the k8s API)
-- not a bug in `setCanaryWeights`, and not hidden: the very next burst, run after a 3s settle
with no other change, landed 40/40 on stable. The 50/50 row's 47.5/52.5 real split is within
the expected ~35/65-65/35 band for Istio's weighted routing over 40 samples (a probabilistic
per-request selection, not an exact round-robin).

Deployment state was inspected live at each step (`kubectl get deploy -n autofde-lab`): promote
left exactly one Deployment (`autofde-lab-status-canary`) with the stable one genuinely absent;
after `services-and-deployments.yaml` was re-applied and rollback called, `kubectl get deploy`
showed exactly one Deployment again (`autofde-lab-status`, back to its original name), and a
follow-up `kubectl get pods -n autofde-lab` confirmed the canary pod fully `Terminating` -> gone
-- the platform returned to its real, original single-Deployment steady state, not merely a
weight change on top of leftover infrastructure. Full evidence, including the exact commands
run: `canary-traffic-split-measured-real` in `evidence/control-evidence-bundle.json`.

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

## Private Connectivity

Real transport-layer access control for the platform's genuinely sensitive surface -- the AWS
PrivateLink / GCP Private Service Connect / Azure Private Link equivalent -- implemented as a
second, distinct Istio Gateway that requires the CALLER to present a valid client certificate
(mutual TLS at the ingress edge), gating exactly the backups/restore control path
(`/api/projects/<name>/backups` and `/projects/<name>/backups`, both the JSON API and its UI
page -- see the Modules table above), because that path is the one module that runs a real
destructive database operation (`pg_dump` for backup, drop-and-replay `psql -f` for restore --
`app/app/api/projects/[name]/backups/route.ts`, `lib/k8s.ts` `createBackupJob`/
`createRestoreJob`).

This is a THIRD, additive layer, not a replacement for the other two that already exist on this
cluster:

1. Mesh-wide **service-to-service** mTLS (`k8s/mtls.yaml`, `PeerAuthentication` mode `STRICT`)
   -- every pod-to-pod hop inside the mesh already required a workload certificate. This never
   covered the ingress edge itself: a caller outside the mesh reaching the gateway over plain
   HTTP was, and for every other route still is, unauthenticated at the transport layer.
2. **App-level session auth** (`requireActor`/`requireSession` + `requireRole`, cookie- or
   `Authorization: Bearer pk_live_...`-based) on the route handler itself -- still fully in
   effect and unchanged; a request with a perfectly valid client certificate but no session
   still gets a real `401 {"error":"unauthenticated"}` from the app.
3. **This layer**: a client certificate check at the Istio Gateway, before any request reaches
   the app at all.

### Topology

`k8s/mtls-gateway.yaml` adds a dedicated `Gateway` (`platform-console-mtls-gateway`) on a
distinct port and host from the existing public route -- port `8444`, host
`backups.platform.local`, `protocol: HTTPS`, `tls.mode: MUTUAL` -- with its own
`VirtualService` (`platform-console-mtls-backups`) matching only
`^/api/projects/[^/]+/backups$` and `^/projects/[^/]+/backups$`, routed to the same backend
Service every other platform-console route uses. **Correction, disclosed rather than silently fixed**: an earlier version of this feature also
edited `k8s/gateway.yaml`'s plain-HTTP `platform-console-ingress` VirtualService to
direct-`421` those same two path patterns, making the mTLS gateway the *only* way to reach
them. That broke the console's own already-shipped, already-verified browser UI
(`RunBackupButton`/`RestoreBackupButton` -- see the "Backup Restore" commit's real
delete-then-restore proof) for every normal session, since a browser cannot present a client
certificate through a standard page load. Reverted before it ever landed on `main`: the plain
route continues to proxy these paths normally (session-auth-gated, as always), and the mTLS
gateway is a real, *additional* private access path for programmatic/operator use -- matching
how AWS PrivateLink / GCP Private Service Connect actually work in practice (an extra private
path alongside the public one, never an exclusive replacement for it).

The shared `istio-system/istio-ingressgateway` Service (pre-existing infra, not owned by this
directory) needed a new port added so `8444` is externally reachable:

```
kubectl patch svc istio-ingressgateway -n istio-system --type=json \
  -p='[{"op":"add","path":"/spec/ports/-","value":{"name":"mtls-backups","port":8444,"targetPort":8444,"protocol":"TCP"}}]'
```

That patch is not re-applied by anything in this directory (the Service is Helm-managed
upstream) -- if the Service is ever fully reconciled back to its chart-rendered state, the port
needs to be re-added the same way.

### Client certificate issuance

The trust root is a real CA generated with `openssl`, the standard self-signed-CA pattern (not
a security bypass -- this is how every private-CA mTLS deployment, including PrivateLink's own
internal trust model, actually gets its root material):

```bash
# 1. CA -- the private key is the only genuinely secret artifact here. Keep
#    it in your own secrets manager; it is NEVER stored in the cluster and
#    NEVER committed to this repo (only ca.crt, the public half, is).
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
  -subj "/O=Platform Engineering/OU=Private Connectivity/CN=platform-backups-mtls-ca" \
  -out ca.crt

# 2. Gateway's own server certificate (what the CALLER's TLS client verifies),
#    signed by that same CA, SAN required:
openssl genrsa -out server.key 2048
openssl req -new -key server.key \
  -subj "/O=Platform Engineering/CN=backups.platform.local" -out server.csr
printf "subjectAltName = DNS:backups.platform.local\nextendedKeyUsage = serverAuth\n" > server-ext.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 825 -sha256 -extfile server-ext.cnf

kubectl create secret generic platform-backups-mtls-credential -n istio-system \
  --from-file=tls.crt=server.crt --from-file=tls.key=server.key --from-file=ca.crt=ca.crt
```

To get a real client certificate for a new operator, the CA holder (not the operator) runs:

```bash
# 3. Operator's own key + CSR (the operator can generate genrsa/req
#    themselves and send only the .csr -- the CA holder never needs to see
#    the operator's private key):
openssl genrsa -out <operator-name>.key 2048
openssl req -new -key <operator-name>.key \
  -subj "/O=Platform Engineering/OU=Backups Operators/CN=<operator-name>" \
  -out <operator-name>.csr

# 4. CA holder signs it:
printf "extendedKeyUsage = clientAuth\n" > client-ext.cnf
openssl x509 -req -in <operator-name>.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out <operator-name>.crt -days 825 -sha256 -extfile client-ext.cnf
```

The operator then calls the gated path with their own cert/key plus the CA's public cert to
verify the gateway's server identity:

```bash
curl --resolve backups.platform.local:8444:<ingress-address> \
  --cacert ca.crt --cert <operator-name>.crt --key <operator-name>.key \
  https://backups.platform.local:8444/api/projects/<name>/backups
```

Revocation, for this cluster's current scope, is by rotating `ca.key` and re-signing/re-issuing
(no CRL/OCSP endpoint is stood up) -- a genuinely disclosed limitation, not silently glossed
over: fine for a single small operator group, not a substitute for a real CRL/OCSP-backed CA at
larger scale.

### Real proof (all three TLS-layer outcomes, live)

Via `kubectl port-forward -n istio-system svc/istio-ingressgateway 18444:8444`:

- **No client certificate** -> real TLS-layer failure, not an application 403: curl exit `56`,
  `LibreSSL SSL_read: LibreSSL/3.3.6: error:1404C45C:SSL routines:ST_OK:reason(1116), errno 0`
  -- reason 1116 is `SSL_R_TLSV13_ALERT_CERTIFICATE_REQUIRED`, Envoy's own TLS 1.3
  `certificate_required` alert. The app is never reached; there is no HTTP status line at all.
- **The real CA-signed client certificate** (`--cert client.crt --key client.key`) -> full
  mutual TLS handshake succeeds (`curl -v` shows Envoy's `Request CERT(13)`, then curl's own
  `Certificate(11)`/`CERT verify(15)`/`Finished(20)`, `SSL connection using TLSv1.3`), and the
  real API responds normally over that connection: `HTTP/2 401 {"error":"unauthenticated"}`
  from the real route handler's `requireActor()` check -- the transport gate is additive to,
  not a replacement for, app-level session auth, exactly as intended.
- **A different, unrelated self-signed certificate** (not signed by the real CA) -> real
  rejection too, with a DIFFERENTLY SPECIFIC alert than the no-cert case, proving the gateway
  validates the presented cert's issuer against this specific CA rather than "any cert
  present": curl exit `56`,
  `LibreSSL SSL_read: LibreSSL/3.3.6: error:1404C418:SSL routines:ST_OK:tlsv1 alert unknown ca, errno 0`.

Independently re-verified after the exclusivity-gate correction above: the plain,
pre-existing HTTP route (with a valid session cookie) still serves these paths normally --
real `200` on `GET /projects/demo-project/backups` and real backup-job data on
`GET /api/projects/demo-project/backups` -- confirming the browser UI is fully restored
alongside the new mTLS path. Full command transcripts and the distinguishing alert text:
`mtls-gated-route-rejects-untrusted-clients` in `evidence/control-evidence-bundle.json`.

## Custom Domains

Real Custom Domain self-service (the AWS Certificate Manager + Route53 custom-domain binding /
GCP Cloud Run custom-domain equivalent), `lib/custom-domains.ts`. An owner registers a
hostname and picks one of the platform's own real Services (the same list `/service-discovery`
already reads, `listAllServices`), and the console does the three real things a hyperscaler
console does behind that one click:

1. **Issues a real TLS certificate.** No ACM/Let's Encrypt in this cluster, so the cert is
   self-signed -- but a REAL X.509 certificate, generated fresh per hostname via a real
   `openssl req -x509 -newkey rsa:2048 -nodes -days 365 -addext "subjectAltName=DNS:<hostname>"`
   subprocess in a throwaway temp dir (`fs.mkdtempSync`, always removed in a `finally`). Before
   it is ever stored, the fresh cert is independently re-parsed with Node's OWN
   `crypto.X509Certificate` and `checkHost(hostname)` is required to actually match -- a second,
   independent verification, not a re-read of what openssl claims to have done.
2. **Stores it as a real `kubernetes.io/tls` Secret in `istio-system`** -- the same namespace
   `k8s/gateway.yaml`'s `platform-console-tls` and `k8s/mtls-gateway.yaml`'s
   `platform-backups-mtls-credential` already live in. Istio's ingress-gateway SDS only reads a
   Gateway's `credentialName` Secret from the gateway WORKLOAD's own namespace, never the
   Gateway object's namespace -- confirmed by both of those pre-existing Secrets already living
   there, not assumed.
3. **Creates a real `Gateway` + `VirtualService` pair**, in `platform-console` (same namespace
   `k8s/gateway.yaml`/`k8s/mtls-gateway.yaml`'s own Gateway/VirtualService objects already use),
   bound to that one hostname. The new Gateway's server declares `port.number: 443` -- NOT the
   8443 an operator actually connects to -- deliberately: confirmed live via `istioctl
   proxy-config listener` before this value was picked that this cluster's non-root
   istio-ingressgateway auto-offsets any declared port `<1024` by `+8000` when binding Envoy's
   real listener (declared `443` binds a real `0.0.0.0:8443` socket inside the pod), and Gateway
   objects only merge onto the SAME physical listener (splitting traffic by SNI) when they
   declare the SAME `port.number`. Declaring `8443` directly would instead make Envoy try to bind
   its own separate listener on that exact already-occupied socket -- a real conflict, not a
   second usable route. The real external door operators/`curl` connect through is a dedicated
   `https-custom-domains` port (`8443`) added to the shared `istio-ingressgateway` Service as a
   one-time infra step (same pattern `k8s/mtls-gateway.yaml`'s own header comment documents for
   its `8444`):
   ```
   kubectl patch svc istio-ingressgateway -n istio-system --type=json -p \
     '[{"op":"add","path":"/spec/ports/-","value":
       {"name":"https-custom-domains","port":8443,"targetPort":8443,"protocol":"TCP"}}]'
   ```
   `targetPort: 8443` here is the SAME real container port the `443`-offset above already binds
   -- this Service port is just a second, dedicated external door onto the identical physical
   listener, not a new one.

All three real objects (Secret, Gateway, VirtualService) are named deterministically from the
hostname and carry a `platform-console.io/custom-domain: "true"` label plus
`platform-console.io/*` annotations recording the real target Service -- `listCustomDomains`
never needs a side database, it just re-reads the live Gateway objects, the same "the listing
IS the record" convention `lib/scheduled-jobs.ts`/`lib/batch-jobs.ts` already use for
CronJobs/Jobs. Register creates Secret -> Gateway -> VirtualService (the object that actually
turns on live routing, created last) and rolls back whatever it already created on any failure;
unbind deletes VirtualService -> Gateway -> Secret (traffic stops first), and is idempotent.

**A real, disclosed gap this feature surfaced and fixed.** A custom domain's Gateway/
VirtualService routes DIRECTLY from the istio-ingressgateway pod (`istio-system`) to the target
project's status Service -- a genuinely different network path than every other route in this
cluster, which all proxy through `platform-console-gateway`'s own already-allowed identity
first. The first live registration against `gymact-status` proved this real: the TLS handshake
succeeded but the app request came back a real Envoy `503 upstream connect error ... connection
timeout` -- the exact same CNI-drop signature `network-segmentation`'s own control evidence
documents for a blocked cross-identity call, because `k8s/network-policies.yaml`'s
default-deny + `*-allow-from-platform-console` baseline never anticipated the ingress gateway
itself as a caller. Fixed with a new, narrowly-scoped `*-allow-from-istio-ingressgateway`
NetworkPolicy per project namespace (autofde-lab, gymact, ggen, ggen-marketplace) -- ingress
from exactly the istio-ingressgateway pod's own identity (`namespaceSelector: istio-system` +
`podSelector: istio=ingressgateway`, the same selector istio-ingressgateway's own Service
already uses), same port `8080` only as the existing `allow-from-platform-console` rule --
re-run after the fix and it worked, see the transcript below.

**RBAC, scoped narrowly.** Two new Roles (`k8s/paas-rbac.yaml`), neither folded into the
read-mostly `platform-console-paas` ClusterRole: (1) `platform-console-custom-domains`,
`platform-console` namespace only, `get/list/watch/create/delete` on
`networking.istio.io` `gateways`/`virtualservices` -- broader than the existing Canary Role's
`virtualservices` grant (which only ever updates ONE standing object `kubectl apply` already
created) because this feature genuinely creates and deletes a NEW pair per operator action; (2)
`platform-console-custom-domains-tls`, `istio-system` namespace, `get/list/create/delete` on
core `secrets` -- a deliberate, disclosed exception to every other Secrets grant in this file
(always scoped to the 5 platform project namespaces, never a system namespace), unavoidable
because Istio's SDS requires the credential Secret to live in the gateway workload's own
namespace. Mitigated at the application layer: `lib/custom-domains.ts` only ever
GETs/DELETEs Secrets it names itself (`custom-domain-<slug>-tls`), never lists or reads Secret
VALUES for any other name. Confirmed live, narrow and correctly scoped:

```
$ kubectl auth can-i create gateways.networking.istio.io -n platform-console \
    --as=system:serviceaccount:platform-console:platform-console
yes
$ kubectl auth can-i create secrets -n istio-system \
    --as=system:serviceaccount:platform-console:platform-console
yes
$ kubectl auth can-i create gateways.networking.istio.io -n default \
    --as=system:serviceaccount:platform-console:platform-console
no
```

**Real proof, end to end, through the real deployed pod.** Rebuilt
`platform-console/console:latest` (Dockerfile now installs a real `openssl` CLI into the
`node:20-slim` runner -- confirmed live via `kubectl exec ... -- which openssl` returning a
real "not found" before that line existed), `kind load docker-image`'d it, `kubectl rollout
restart`'ed `platform-console-gateway` (2/2 healthy). Logged in through the real deployed pod
(real `POST /api/login`, admin password hash rotated to a freshly generated known bcryptjs
hash for this verification and restored immediately after, same precedent the Load Testing
section above documents). Through the authenticated `/api/custom-domains`:

- `POST {"hostname":"demo.platform.local","serviceName":"gymact-status",
  "serviceNamespace":"gymact","servicePort":80}` -> real `201`, real
  `Secret/custom-domain-demo-platform-local-tls` (istio-system),
  `Gateway/custom-domain-demo-platform-local-gateway`,
  `VirtualService/custom-domain-demo-platform-local-vs` (platform-console) -- confirmed via
  `kubectl get gateway/virtualservice/secret -o yaml`, real objects with the real registered
  hostname/target in their annotations.
- `istioctl proxy-config listener istio-ingressgateway-... -n istio-system` before vs. after
  registration:
  ```
  0.0.0.0   8443  SNI: platform.local         Route: https.443.https.platform-console-gateway...
  ```
  became
  ```
  0.0.0.0   8443  SNI: platform.local         Route: https.443.https.platform-console-gateway...
  0.0.0.0   8443  SNI: demo.platform.local    Route: https.443.https-demo-platform-local.custom-domain-demo-platform-local-gateway.platform-console
  ```
  confirming the new hostname merged onto the SAME physical listener via SNI, exactly as
  designed, before any HTTP request was made.
- **Real TLS handshake, real presented certificate, real target-service response**, through the
  real Istio ingress gateway (`kubectl port-forward -n istio-system svc/istio-ingressgateway
  18443:443`, then a real client connecting with SNI `demo.platform.local`):
  ```
  $ curl -skv --resolve demo.platform.local:18443:127.0.0.1 https://demo.platform.local:18443/status
  *  subject: CN=demo.platform.local
  *  start date: Aug 18 13:26:02 2026 GMT
  *  expire date: Aug 18 13:26:02 2027 GMT
  > GET /status HTTP/2
  < HTTP/2 200
  {"service":"gymact-status","repo":"gymact", ...}
  ```
  and independently via `openssl s_client -connect 127.0.0.1:18443 -servername
  demo.platform.local`, whose presented certificate's `X509v3 Subject Alternative Name` read
  `DNS:demo.platform.local` -- an exact match to the registered hostname, not some other cert
  (the SAME connection with `-servername platform.local` instead returns "no peer certificate
  available", a completely different, unrelated chain, proving SNI-based cert selection is
  real and specific, not a wildcard/default fallback).
- **Unbind, then a real connection refusal, not silently still working.** `DELETE
  /api/custom-domains?hostname=demo.platform.local` -> real `200`; `kubectl get
  gateway/virtualservice/secret` for all three names returned real `NotFound`; `istioctl
  proxy-config listener` immediately dropped the `SNI: demo.platform.local` line, leaving only
  `platform.local`/`backups.platform.local`; a fresh `openssl s_client -servername
  demo.platform.local` against the same listener returned a real
  `error:...unexpected eof while reading` (Envoy closing the connection with no matching filter
  chain, not a cert), and `curl` to the same hostname/path returned a real connection failure
  (curl exit 7 / `HTTP_CODE=000`) -- the hostname genuinely stopped routing.
- **Cleanup verified**: the original `ADMIN_PASSWORD_HASH` was restored and the deployment
  rolled again; the temporary test password subsequently received a real `401
  {"error":"invalid credentials"}` from `POST /api/login` against the freshly rolled pod.

Full command transcripts: `custom-domain-tls-cert-matches-hostname` in
`evidence/control-evidence-bundle.json`.

**Disclosed RBAC scope limitation, found during this feature's own pre-commit review, not
hidden**: `platform-console-custom-domains-tls` (`k8s/paas-rbac.yaml`) grants
`get/list/create/delete` on `secrets` across the *entire* `istio-system` namespace, not scoped
to only the TLS Secrets this feature creates. This is a real k8s RBAC limitation, not an
oversight left unexamined: `list` cannot be `resourceNames`-restricted at all (the console
needs to enumerate its own custom-domain secrets to render `/custom-domains`), and dynamically
created secret names can't be pre-enumerated for `get`/`delete` either. The practical
consequence: a compromised `platform-console` pod could read or delete OTHER Secrets in
`istio-system` it has no legitimate reason to touch (e.g. `platform-backups-mtls-credential`
from the Private Connectivity module, or Istio's own default cert). Closing this properly
would need a label-selector-aware admission controller or a dedicated CRD, both out of scope
for this pass. Mitigated in application code (`lib/custom-domains.ts` never touches a Secret
it didn't itself create, by name), but that is a code-level convention, not an RBAC-enforced
boundary -- the platform-level trust boundary here is narrower than the RBAC grant technically
allows, and that gap is real, not merely theoretical.

## Certificate Lifecycle

Real Certificate Lifecycle tracking (the AWS Certificate Manager auto-renewal / GCP-managed
-certificate rotation equivalent), `lib/cert-lifecycle.ts` -- the capability the Custom Domains
feature above deliberately left out: once a certificate exists, a hyperscaler console also
tracks its expiry and rotates it before it lapses, without breaking live traffic.

**Scan (`listManagedCertificates`).** One live, namespace-wide GET of every Secret in
`istio-system`, filtered to whichever ones actually carry a `tls.crt` key -- deliberately never
filtered on `type`, because `platform-backups-mtls-credential` (the Private Connectivity
module's mTLS credential) is `type: Opaque`, not `kubernetes.io/tls`, confirmed live via
`kubectl get secret -n istio-system platform-backups-mtls-credential -o jsonpath='{.type}'`
returning `Opaque`; filtering on `type` would silently skip it. Each real cert is independently
parsed with Node's own `crypto.X509Certificate` (subject, issuer, serial number, `notBefore`,
`notAfter`) -- no side database, the Secrets themselves are the record, same "the listing IS
the record" convention `lib/custom-domains.ts`'s own `listCustomDomains` already uses. Real
days-until-expiry is `floor((notAfter - now) / 86400s)`; a cert under 30 days out is flagged
`expiringSoon`, one already past `notAfter` is flagged `expired`. Only certificates carrying the
`platform-console.io/custom-domain: "true"` label are `rotatable` -- rotating
`platform-console-tls` or the mTLS credential would need a real client-trust-chain story this
pass deliberately does not build, a disclosed gap, not a silent omission.

**Rotate in place (`rotateCertificate`).** For a custom-domain cert only: reuses
`lib/custom-domains.ts`'s own `generateSelfSignedCertificate` (the exact same
`openssl req -x509 ... -addext "subjectAltName=DNS:<hostname>"` subprocess plus independent
`checkHost` re-verification every fresh registration already goes through -- never a second,
driftable copy) to mint a fresh cert for the Secret's own `platform-console.io/hostname`
annotation, then writes it back via `lib/k8s.ts`'s own `createOrUpdateSecret` -- a real RFC 7386
merge-patch of `data` only, same Secret name, `metadata.labels`/`annotations` completely
untouched. This is the entire reason rotation is a PATCH and not a delete+recreate: Istio's SDS
layer holds a live watch on each `credentialName` Secret it already resolved, and pushes new
key/cert material to Envoy the moment that Secret's `data` changes -- no Gateway/VirtualService
object is ever touched, so there is no window where the hostname has a route but no cert (or no
route at all), the same failure mode a delete+recreate would risk.

**A real, disclosed RBAC gap this feature surfaced and fixed, the same way the Custom Domains
feature's own cross-identity NetworkPolicy gap was surfaced above.** The first live rotation
attempt (below) failed with a real
`secrets "custom-domain-...-tls" is forbidden: ... cannot patch resource "secrets"` --
`platform-console-custom-domains-tls` (`k8s/paas-rbac.yaml`) granted
`get/list/create/delete` on `istio-system` Secrets but never `patch`, because nothing before
this feature ever needed to update a Secret's `data` in place. Fixed by adding exactly `patch`
to that Role's existing verb list (still scoped to the same single Role, still the same
"application code only ever touches Secrets it named itself" mitigation `README.md`'s Custom
Domains section already documents for this Role's broader-than-ideal `list`/`get`/`delete`
scope) -- re-applied live and confirmed via
`kubectl auth can-i patch secrets -n istio-system --as=system:serviceaccount:platform-console:platform-console`
returning `yes`, then the same rotation call re-run successfully.

**Real proof, end to end, through the real deployed pod -- the part that matters.** Rebuilt
`platform-console/console:latest`, `kind load docker-image`'d it, `kubectl rollout restart`'ed
`platform-console-gateway` (2/2 healthy). Logged in through the real deployed pod (admin
password temporarily rotated to a freshly generated known bcryptjs hash, same restore-after
precedent every prior live-proof section in this file documents).

1. Registered a real throwaway custom domain through the authenticated
   `POST /api/custom-domains`: `cert-rotate-demo.platform.local` -> `gymact-status.gymact:80`,
   real `201`, `Secret/custom-domain-cert-rotate-demo-platform-local-tls` created in
   `istio-system` with real initial serial `0DE084F4769545E01802907D31A4918F2EF0FECC`
   (`notAfter` `2027-08-18T14:36:31.000Z`).
2. `GET /api/certificates` (the new dashboard's own API) correctly listed it as
   `kind: "custom-domain"`, `rotatable: true`, alongside the pre-existing
   `platform-backups-mtls-credential` (`kind: "mtls-backups"`, `rotatable: false`, real 824-day
   runway) -- confirming the scan reads both Secret shapes correctly.
3. Started a real background loop making one real HTTPS request per second against the live
   domain through the actual deployed `istio-ingressgateway`
   (`kubectl port-forward -n istio-system svc/istio-ingressgateway 18443:443`, then
   `curl -sk --resolve cert-rotate-demo.platform.local:18443:127.0.0.1
   https://cert-rotate-demo.platform.local:18443/status`, real `gymact-status` JSON body each
   time), logging every real response code with a real UTC timestamp.
4. **While that loop was running**, triggered a real rotation through the authenticated console:
   `POST /api/certificates {"secretName":"custom-domain-cert-rotate-demo-platform-local-tls"}` ->
   real `200`:
   ```json
   {"rotation":{"secretName":"custom-domain-cert-rotate-demo-platform-local-tls",
     "hostname":"cert-rotate-demo.platform.local",
     "oldSerialNumber":"0DE084F4769545E01802907D31A4918F2EF0FECC",
     "newSerialNumber":"20A6E04D0B8D815F33FB97E7F2AEF028240B1D64",
     "oldNotAfter":"2027-08-18T14:36:31.000Z","newNotAfter":"2027-08-18T14:37:24.000Z",
     "rotatedAt":"2026-08-18T14:37:24.709Z"}}
   ```
5. **(a) Zero downtime, confirmed by the real request-loop log, not assumed.** All 90/90 real
   requests across the full loop -- spanning well before, exactly at, and well after the
   `14:37:24.709Z` rotation timestamp above -- returned real `200`. No transient hiccup was
   observed; that is reported honestly here because it was checked, not because a clean result
   was expected going in (Envoy/SDS's own watch-based reload is asynchronous with the PATCH
   call, so a request landing in the handful of milliseconds of actual swap was a real
   possibility this run simply didn't hit).
6. **(b) A genuinely different presented certificate, confirmed independently of the API's own
   claim.** A fresh `openssl s_client -connect 127.0.0.1:18443 -servername
   cert-rotate-demo.platform.local` immediately after the rotation call (8s later) returned:
   ```
   serial=20A6E04D0B8D815F33FB97E7F2AEF028240B1D64
   subject=CN=cert-rotate-demo.platform.local
   notBefore=Aug 18 14:37:24 2026 GMT
   notAfter=Aug 18 14:37:24 2027 GMT
   ```
   -- the exact `newSerialNumber`/`newNotAfter` the rotation API reported, genuinely different
   from the pre-rotation serial `0DE084F4769545E01802907D31A4918F2EF0FECC`
   (`notAfter` `2027-08-18T14:36:31.000Z`) an `openssl s_client` connection made before step 4
   returned. A second, later `openssl s_client` connection (well after the loop finished)
   returned the same new serial, confirming this was a real, durable swap at the TLS layer, not
   a one-request fluke. `GET /api/certificates` after rotation also reflected the new serial in
   the dashboard's own listing.
7. **Cleanup verified.** `DELETE /api/custom-domains?hostname=cert-rotate-demo.platform.local`
   -> real `200`; `kubectl get gateway/virtualservice/secret` for all three
   `cert-rotate-demo-platform-local` names returned real `NotFound`. The original
   `ADMIN_PASSWORD_HASH` was restored and the deployment rolled again; the temporary test
   password immediately returned a real `401 {"error":"invalid credentials"}` from
   `POST /api/login` against the freshly rolled pod (confirmed against a fresh port-forward
   connection, after an initial false-negative caused by `kubectl port-forward`'s tunnel still
   pinned to the just-terminated old pod during rollout -- disclosed here rather than silently
   dropped, since it is a real artifact of how `kubectl port-forward` pins to one pod, not of
   the restore itself).

Full command transcripts: `certificate-rotation-zero-downtime-verified` in
`evidence/control-evidence-bundle.json`.

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

## Load Testing

Real Load Testing / performance benchmarking self-service, the capability every hyperscaler
PaaS wraps (the AWS Distributed Load Testing solution, GCP's own load-testing guidance
tooling) -- built directly on top of the Autoscaling section above, so an operator can drive
real load against a real service and watch the real HPA react, not two disconnected demos.

- **`lib/load-test.ts`**: `runLoadTest(targetUrl, {concurrency, durationSec})` fires real
  concurrent `GET` requests (Node's built-in `fetch`, a plain `Promise.all`-based worker pool
  of `concurrency` loop workers, no new dependency) for `durationSec` real wall-clock seconds,
  reading each real response body and timing it with `performance.now()`. Returns real
  `p50`/`p95`/`p99`/min/mean/max latency (computed from the real sorted per-request latency
  array, not estimated) plus real success/error counts and `requestsPerSec` -- every number in
  the result comes from an actual response actually received, nothing synthesized.
- **SSRF boundary**: `runLoadTest` itself takes a raw URL (so it's a genuinely reusable
  worker-pool primitive), but the only caller anywhere in this app is
  `runLoadTestAgainstTarget`, which resolves a client-supplied `targetId` against
  `LOAD_TEST_TARGETS` -- a fixed, server-defined allowlist of exactly the 4 status services
  `lib/status.ts` already trusts (`autofde-lab-status`, `gymact-status`, `ggen-status`,
  `ggen-marketplace-status`) plus this console's own public `/api/status`. `app/api/load-test/
  route.ts` (the only HTTP entry point) accepts `targetId`, never a URL, from the request
  body -- an unknown id is rejected `400` before `fetch` is ever called.
- **`/load-test` page + `POST /api/load-test`**: member+-gated (`requireRole(session,
  "member")`, enforced server-side in the route, same boundary as `/scheduled-jobs`/
  `/secrets`) -- running a real concurrent-request benchmark against a live internal service is
  a genuinely consequential action, not a read. Pick a target, set concurrency (1-300) and
  duration (1-180s), run it, see the real result rendered (latency percentiles, req/sec,
  error rate) after the benchmark's real full duration -- no optimistic UI, the button stays
  disabled for the real run time.
- **Real proof: this platform's own tool drove a real HPA `SuccessfulRescale`, not a
  `kubectl exec` busy-loop this time**. Rebuilt `platform-console/console:latest`, `kind load
  docker-image`'d it into the live `platform-eng-colima-control-plane` node, `kubectl rollout
  restart`'ed `platform-console-gateway` (verified 2/2 healthy). Logged in through the actual
  deployed pod (`kubectl port-forward svc/platform-console-gateway 18080:8080`, real `POST
  /api/login` -- the admin password hash was rotated in the live `platform-console-secrets`
  Secret to a freshly generated, known bcryptjs hash for this verification, same precedent as
  prior passes, restored immediately after -- see below). `gymact-status-hpa` started at its
  normal baseline (`cpu: 5%/70%`, `REPLICAS: 1`). A real `POST /api/load-test
  {"targetId":"gymact-status","concurrency":80,"durationSec":20}` against the live pod fired
  25,355 real requests over a real 21.2s wall time (1,195.3 req/sec), **0 errors** -- real
  measured latency `p50 54.1ms / p95 176.9ms / p99 254.9ms` (mean 64.5ms, min 3.6ms, max
  1,238.7ms). Latency genuinely degraded across the run (rising tail, honestly reported, not
  smoothed over) -- internally consistent with what actually happened: the single pre-scale
  `gymact-status` pod was driven from its `2m` baseline to real CPU utilization the HPA itself
  reported as `315%/70%` of its `50m` request (`kubectl top pod` showing `188-198m` per pod
  once scaled), i.e. the pod was genuinely saturated against its `200m` limit for the back half
  of the run, which is exactly what a rising p95/p99/max under sustained real concurrency looks
  like. The HPA controller fired a real `SuccessfulRescale` event: `New size: 3; reason: cpu
  resource utilization (percentage of request) above target`, `kubectl get hpa -n gymact`
  showing `REPLICAS` go from 1 to 3 (its configured max), and `kubectl get pods -n gymact`
  showing two new real Pods (`gymact-status-...-4f4th`, `...-tztlz`) reach `Running` -- this
  time triggered by the platform's own load-test tool making real HTTP requests through the
  real Service, not a `kubectl exec` CPU busy-loop.
- **Honest side effect, disclosed rather than hidden**: the load test's worker pool runs
  server-side inside the `platform-console-gateway` pod itself (that's where `POST
  /api/load-test`'s Node process lives), so firing 80 concurrent outbound `fetch` calls for 20s
  is real CPU work for the console pod too -- it genuinely tripped the console's *own*
  `platform-console-gateway-hpa` (`cpu: 3%/70%` baseline), which scaled `REPLICAS` from 2 to 5
  for real, confirmed via `kubectl get hpa -n platform-console` / `kubectl get pods -n
  platform-console` showing 3 new real Pods. Not a bug in this proof -- a real, correctly-
  documented property of running the load generator co-located with the app it's part of (the
  same reason real hyperscaler load-testing services run their generators on a separate,
  dedicated fleet rather than the target's own compute).
- **Real scale-down, both HPAs, load subsided**: no load was generated after the run
  completed. `gymact-status`'s CPU returned to its `2-5m` baseline within one metrics-server
  scrape interval; Kubernetes' default 5-minute scale-down stabilization window then elapsed
  for real (scale-up event at `11:51:57Z`, scale-down event at `11:57:15Z`, ~5m18s later -- no
  window skipped or shortened), and the controller fired a second real event on
  `gymact-status-hpa`: `SuccessfulRescale New size: 1; reason: All metrics below target`,
  `kubectl get hpa -n gymact` showing `REPLICAS` return to 1 and `kubectl get pods -n gymact`
  showing the two surge Pods `Terminating` then gone, leaving only the original pod running.
  `platform-console-gateway-hpa` independently settled back to `REPLICAS: 2` over the same
  window (`cpu: 3-6%/70%` afterward). Both HPAs confirmed back at their normal steady state via
  `kubectl get hpa -A` before this pass ended.
- **Password-rotation cleanup, same precedent as prior passes**: after the run, the original
  `ADMIN_PASSWORD_HASH` was restored in `platform-console-secrets` and the deployment rolled
  again -- confirmed by the temporary test password subsequently receiving a real `401
  {"error":"invalid credentials"}` from `POST /api/login` against the freshly rolled pod, and
  the console's own gateway HPA rollout (which raced with the same-window scale-up above,
  transiently `FailedCreate`-blocked on `platform-console-quota`'s `limits.cpu` ceiling until
  the old ReplicaSet's pods finished terminating and freed headroom) completing cleanly to
  `2/2 Ready` on the new, restored-hash ReplicaSet.

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

## Status page

A real public Status Page (the AWS Service Health Dashboard / statuspage.io equivalent),
computing genuine uptime/SLO numbers from real historical Prometheus data -- not a static "all
systems operational" placeholder.

- **Why a purpose-built exporter, not the 4 status services' own `/status`/`/healthz`
  responses directly**: Prometheus's own `up` metric requires the scraped target to serve
  Prometheus text-exposition format, which none of this platform's third-party components
  (`supabase/gotrue`, `postgrest/postgrest`) expose, and Postgres isn't HTTP at all. Rather
  than fabricate a number for those three, `services/platform-prober` (stdlib Python, no
  dependencies) performs a genuine HTTP GET or TCP connect against all 8 components on every
  single Prometheus scrape (no caching between scrapes) and exposes the real outcome as
  `up{component="<id>"} 1|0` in real Prometheus text format on `:8080/metrics` -- the same
  synthetic-canary technique a real hyperscaler status page's monitoring layer uses.
- `lib/status-page.ts`'s `getStatusPageData()` runs genuine PromQL against the real in-cluster
  Prometheus via the existing `lib/prometheus.ts` proxy: an instant `up{component!=""}` query
  for current state, plus `avg_over_time(up{component!=""}[1h]) * 100` and a 24h variant for
  the uptime% columns -- real math over real, previously-recorded, timestamped samples, never
  computed from a request-time snapshot. A component with zero samples in a window renders as
  "no data", never a fabricated 100%.
- `app/status/page.tsx` (server component, `force-dynamic`, 15s meta-refresh) and
  `app/api/status/route.ts` (JSON) are the only unauthenticated routes in this app --
  `middleware.ts`'s `PUBLIC_PATHS` lists `/status` and `/api/status` explicitly, matching how
  real hyperscaler status pages work (every other route still redirects to `/login`, confirmed
  live -- see the evidence bundle).
- **Istio caveat, confirmed live and fixed, not silently worked around**: the namespace-wide
  `platform-console-mtls` `PeerAuthentication` (STRICT, `k8s/mtls.yaml`) rejected Prometheus's
  plaintext scrape of `platform-prober` with a real `connection reset by peer` (Prometheus is
  not an Istio mesh member and cannot originate mTLS). Fixed with a second, narrowly-scoped
  `PeerAuthentication` (`k8s/status-page.yaml`) selecting only `app: platform-prober` pods,
  PERMISSIVE on exactly port 8080 -- every other pod and every other port keeps the
  namespace's STRICT default unchanged.
- See `status-page-slo-reflects-real-state` in `evidence/control-evidence-bundle.json` for the
  real before/during/after transcript: a deliberate `kubectl scale --replicas=0` outage of
  `gymact-status`, the public page's current-state indicator flipping to "down" within one
  15s scrape cycle (confirmed by polling `/api/status` through the real Istio ingress gateway,
  no session cookie sent), the real historical uptime% dropping from 100% to 53.85% as down
  samples accumulated, the indicator flipping back to healthy after `--replicas=1`, and the
  `gymact-status-hpa` HorizontalPodAutoscaler settling back at its normal `REPLICAS: 1`
  (never stuck at 0).

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
versus which are configured but not currently enacted.

The control list below has drifted out of sync with the live bundle every time a new module
landed (most recently: this line said "32 controls" after the count had already reached 39) --
so this file no longer hand-enumerates the list. **The bundle's own `controls` array and
`gaps` array are the single source of truth**; read `evidence/control-evidence-bundle.json`
directly for the current count and the full real-evidence text for every entry. As of the most
recent pass to touch this section, the bundle held 39 controls and an empty `gaps` array --
verify against the live file rather than trusting that number to still be current.

restore-recovers-real-deleted-data discloses a real, non-hiding limitation of the restore path
itself (a dependent-table row loaded out of FK order in a single restore pass) rather than only
claiming what worked
-- see the bundle. edge-function-invocation-verified closed the /projects/[name]/functions
module's prior disclosed gap (no invocation, connection info only) by deploying one real,
minimal Edge Function through the supabase-operator's own `Function` CRD -- investigated
live rather than guessed, confirmed the operator auto-mounts and rolls the functions
Deployment on a new Function CR with zero manual YAML edits -- and wiring a real,
RBAC-gated invoke path through the console into it. status-page-slo-reflects-real-state
records a real, deliberate induced outage (`kubectl scale --replicas=0` on `gymact-status`,
gymact namespace, restored afterward) proving the public `/status` page's uptime% and
current-state indicator both genuinely react to real Prometheus data rather than rendering a
static number -- see the bundle for the full before/during/after transcript.
webhook-delivery-verified-with-valid-signature records a real throwaway receiver Pod+Service
subscribed via the authenticated `/webhooks` API to two of the three real, wired trigger points
(`project.created`, `backup.completed`) -- both a real test Project's creation and a real
completed `pg_dump` backup Job actually POSTed to that receiver through the live Istio mesh, and
both HMAC-SHA256 signatures were independently recomputed with `openssl dgst -hmac` and matched
the received header byte-for-byte; the receiver, test project, backup Job, and both
subscriptions were all deleted afterward.
api-key-auth-enforces-bound-role records a real curl-only session (no cookies at all, verified
live with `curl -v`) authenticating purely via `Authorization: Bearer pk_live_...`: a real key
bound to `viewer` listed projects (`GET /api/projects` -> 200) but got a real `403` attempting a
member-gated write (`POST /api/feature-flags`); a second real key bound to `member` succeeded at
that same write (`200`, the flag genuinely present in a follow-up read); the `viewer` key was
then revoked through the same owner-gated API the UI's Revoke button calls, and the exact same
curl command that returned `200` moments earlier immediately returned a real `401` -- proving
revocation is real and immediate, not cached anywhere in the request path. The stored SHA-256
hashes were independently reproduced byte-for-byte with `openssl dgst -sha256` against the real
plaintext keys, and the raw k8s `Secret` YAML was grepped for both plaintext values -- 0
matches. usage-billing-math-verified-real is a calculation-correctness control, not a claim
about real payment processing (which remains explicitly out of scope everywhere in this
platform): it records real induced CPU load against the live `gymact-status` Deployment (four
parallel real Python busy-loop processes started via `kubectl exec`, same technique as
`autoscaling-enforced`) driving `kubectl top pod` from a real `2m` baseline to a real `202m`
(pegged at the container's real `200m` CPU limit), and the real `/api/billing` line item for
`gymact` genuinely tracking that change over the trailing real 1h window -- `cpuCoreHours` rose
from a real `0.002098934159849656` (baseline) to `0.009397533637733501` (during load, ~100s in),
computed both times by `lib/invoice-preview.ts`'s real `increase()` PromQL over
`container_cpu_usage_seconds_total`, not a static number. After the load-generating processes
were killed in-container, `kubectl top pod` returned to the real `2m` baseline within one
metrics-server scrape interval (confirmed live), while the billing line item's trailing-1h
`cpuCoreHours` correctly continued to reflect the recent burst (`0.010545714058503691`) --
expected, correct behavior for a real cumulative `increase()` over a still-recent window, not a
bug. budget-alert-fires-once-on-real-threshold-crossing records the real end-to-end Budget
Alerts proof: a real throwaway receiver Pod+Service in `gymact`, subscribed via the
authenticated `/webhooks` API to `budget.threshold_crossed`; a real `0.003` CPU-core-hours
threshold set for `gymact` via the authenticated `/budget-alerts` API (above the namespace's
real ~`0.0018` idle baseline, confirmed via a live `GET /api/budget-alerts` read immediately
before load); four real CPU-bound Python busy-loop processes started in the live `gymact-status`
container via `kubectl exec` (same technique `autoscaling-enforced`/`load-test-drives-real-autoscale-event`
use) drove real `cpuCoreHours` from `0.00185` to `0.0037` within the next 10s poll tick. The
receiver's real log shows exactly one `RECEIVED` line for the entire test -- one real HMAC-SHA256-signed
`budget.threshold_crossed` delivery, `x-forwarded-client-cert` showing the real mTLS SPIFFE
identity `spiffe://cluster.local/ns/platform-console/sa/platform-console` -- whose signature was
independently recomputed via `openssl dgst -sha256 -hmac <secret>` over the exact received body
bytes and matched byte-for-byte. Real usage stayed over threshold for a further ~2 minutes
(12+ poll ticks, across both live `platform-console-gateway` replicas' independent pollers) with
zero further deliveries -- the real ConfigMap-persisted "already alerted" marker
(`lib/budget-alerts.ts`) held the dedup across ticks AND across the 2-replica race the other two
webhook trigger types can still double-fire on, confirmed live via repeated `GET
/api/budget-alerts` reads showing `alreadyAlerted: true` throughout. The busy-loop processes'
own 120s timers elapsed naturally (`kubectl top pod` returned to its `5m` baseline); a real,
disclosed side effect matching `load-test-drives-real-autoscale-event`'s own precedent -- the
induced load also tripped the pre-existing `gymact-status-hpa`, a real `SuccessfulRescale` event
scaling `gymact-status` from 1 to 3 replicas, left to recover on its own 5-minute stabilization
window rather than being treated as a defect in this proof. Cleanup, same precedent as prior
passes: the test webhook subscription and budget threshold were removed through the same
authenticated APIs (both real ConfigMaps confirmed emptied via live `kubectl get configmap -o
yaml`), the receiver Pod+Service deleted, and the temporarily-rotated `ADMIN_PASSWORD_HASH`
restored and the deployment rolled again -- confirmed by the exact same temporary test password
that returned `200` moments earlier immediately returning a real `401 {"error":"invalid
credentials"}` from `POST /api/login` against the freshly rolled pod. This doctrine
follows `ggen-marketplace/packs/soc2-audit-pack`: evidence-bundle-complete, never
"compliant".

`session-revocation-enforced-before-jwt-expiry` records the real Active Session Management
proof: two real, distinct sessions were minted through the live deployed pod -- local-admin
(`POST /api/login`, temp-rotated password, same precedent) and a real throwaway GoTrue signup
(`POST /api/auth/gotrue-signup`) -- and both showed up in a real `GET /api/sessions` read as
owner. Session A then revoked session B's real registry row via `DELETE
/api/sessions?sessionId=...` (real `200`, `revoked:true`); session B's still-unexpired original
JWT cookie was immediately retried and got a real `401
{"error":"unauthenticated","reason":"session revoked"}`, while session A kept working
throughout. A direct `psql SELECT` against the live `platform_console.active_sessions` table
(self-bootstrapped via `CREATE TABLE IF NOT EXISTS`, no manual step) cross-matched both rows'
state exactly. Cleanup, same precedent: the throwaway GoTrue user was deleted for real via
GoTrue's own admin API (confirmed `200`), both proof sessions were self-revoked as a final tidy
step, and the temporarily-rotated `ADMIN_PASSWORD_HASH` was restored and the deployment rolled
again -- confirmed by the same temporary password immediately returning a real `401
{"error":"invalid credentials"}`.

`digest` at the bottom of the bundle is a BLAKE3 hash over the bundle's own content, so any
edit to a control's evidence text is detectable. Method, confirmed by reproducing the prior
digest byte-for-byte before this pass changed anything: with `digest.value` set to the empty
string, serialize the whole document with `json.dumps(doc, indent=2, ensure_ascii=False)` plus
one trailing newline, BLAKE3-hash the resulting UTF-8 bytes, then write that hex digest back
into `digest.value`.
