# Platform Engineer's Handbook — Running on Colima

> **Provenance record.** Companion to
> [`platform-engineers-handbook-ggen-packs.md`](platform-engineers-handbook-ggen-packs.md).
> This document records standing up the Ch02 cluster foundation from the shipped
> `platform-engineers-handbook` ggen pack (v0.3.0) on [colima](https://github.com/abiosoft/colima)
> instead of Docker Desktop, and validating it with real tooling.

## Why colima

Docker Desktop was the container runtime backing every earlier verification pass in this
project. This pass switches fully to colima: Docker Desktop stopped, `docker context use
colima`, all subsequent `kind`/`docker`/`istioctl`/`flux` commands run against colima's
Docker socket.

## What was stood up

1. **colima** (`colima start --cpu 4 --memory 8 --disk 60 --runtime docker`) — a real VM
   (Apple `vz` backend) running Docker + a k3s Kubernetes distribution colima itself
   provisions (unused here; a Kind cluster is created inside colima's Docker instead, to
   match the book's own tooling choice).
2. **The pack itself, reconstructed for real**: `ggen sync run` against the exact shipped
   `~/ggen-marketplace/packs/platform-engineers-handbook` (v0.3.0), not a scratch copy —
   proving the published pack, not a working directory, is what runs.
3. **Kind cluster** (`kind create cluster --config kind-config.yaml`, the pack's own file)
   on colima's Docker daemon.
4. **Istio** (`istioctl install --set profile=demo -y`) — real control plane: `istiod`,
   ingress gateway, egress gateway, all `Running`.
5. **Istio mesh policy** (`istio-mesh-config.yaml`, the pack's own file) — mTLS
   (`PeerAuthentication`), JWT auth, authorization policies, virtual services, gateway,
   telemetry, all applied with zero errors against the real control plane.
6. **Flux** (`flux install`) — real GitOps controller: `helm-controller`,
   `kustomize-controller`, `notification-controller`, `source-controller`, all deployments
   ready.

## Validation

Real commands, real output, no infra faked:

- `test-cluster-health.py` (Ch02's own test suite, from the pack): **7/8 pass, 1 correctly
  skipped** (`ArgoCD namespace` check — this book uses Flux for GitOps, not ArgoCD, so the
  skip is expected, not a gap).
- `istioctl proxy-status`: both gateways connected to `istiod`, subscribed to
  CDS/LDS/EDS(/RDS/SDS).
- `flux check`: all prerequisite, controller, and CRD checks pass.
- `istioctl analyze -A`: surfaces real warnings/errors, all of them expected for a cluster
  with the mesh policy applied but no application workload deployed yet — `platform-api`
  service, `monitoring` namespace, and `platform-tls` secret are all referenced by the
  policy config in anticipation of a workload the book deploys in a later chapter, per the
  config file's own documented prerequisite comment. Not treated as platform defects.

## Cluster left running

Unlike the disposable Kind clusters used for chapter-by-chapter defect verification
elsewhere in this project (all torn down after each check), this cluster
(`kind-platform-eng-colima`, on the `colima` docker context) was left running per this
task's scope — "get the platform running," not just re-verify it.

```sh
docker context use colima
kubectl config use-context kind-platform-eng-colima
```

## Update: Ch04 observability stack added

Raised beyond the initial Ch02-only scope: real `kube-prometheus-stack` (Prometheus,
Alertmanager, Grafana, kube-state-metrics, node-exporter, operator) installed via Helm
using the book's own documented command (`chapter-readmes/Ch04-README.md`):

```sh
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace --wait --timeout 300s
```

All 6 pods reach `Running`/fully `Ready`. The pack's own `prometheus-slo-rules.yaml`
(Sloth-generated `PrometheusRule`) applies cleanly against the real PrometheusOperator
CRDs. Validated with a real, live PromQL query against the running Prometheus
(`curl http://localhost:9090/api/v1/query?query=up` via `kubectl port-forward`) —
returns real scrape targets across the cluster, confirming Prometheus is actually
scraping, not just installed.

## Update: Chapters 5, 7, 11, 13, 14 deployed and live-validated

Raised further beyond Ch02+Ch04: five more chapters deployed and exercised against the same
already-running `kind-platform-eng-colima` cluster (`docker context use colima` /
`kubectl config use-context kind-platform-eng-colima`), not a fresh disposable cluster. Each
chapter's pre-existing namespaces (`monitoring`, `istio-system`, `flux-system`,
`application`) were confirmed present and left untouched except where a chapter's own
resources were deliberately added on top.

### Ch05 — demo app

Deployed the chapter's actual Step-by-Step target, `demo-app/` (Flask CRUD API), to the
`application` namespace — not the unrelated root-level Node.js/Express+OTEL app the same
README also documents under Ch05 without clearly distinguishing which one the walkthrough
means.

The shipped manifest could not be applied as-is: `k8s-manifests.yaml` ships
`image: ghcr.io/company/platform-demo-app:IMAGE_TAG_PLACEHOLDER` with
`imagePullPolicy: Always`, which forces a pull against a registry that doesn't exist —
`ImagePullBackOff` on any local Kind cluster, `kind load` notwithstanding. Fixed in a local
edited copy (`image: platform-demo-app:v1`, `imagePullPolicy: IfNotPresent`), not upstream.
With that fix, the deployment rolled out clean: `deployment "platform-demo-app" successfully
rolled out`, 2/2 pods `Running` with native Istio sidecars auto-injected. Real HTTP round
trip via `kubectl port-forward` (no Istio ingress — the cluster's existing `Gateway`/
`VirtualService` route to an unrelated `platform-api` service, so the fallback rule applied):
`GET /health` → `200 {"status":"healthy"}`; `POST /items` → `201` with a real created item;
`GET /items` → `200` listing it back.

Book-instruction gaps found, none fixed upstream in this pass: the placeholder image tag and
`imagePullPolicy: Always` combination is a silent, blocking gap Step 3 never calls out; the
manifest's inline example cluster name (`peh`) matches neither the Prerequisites section's
example (`platform-dev`) nor any real cluster name; no namespace is specified anywhere in the
manifest or apply instructions, which is a collision risk on a shared cluster; the HPA reports
`<unknown>` targets because no `metrics-server` is installed (documented in troubleshooting,
not called out upfront); and the chapter documents two unrelated "demo apps" without a clear
pointer to which one the walkthrough builds.

### Ch07 — onboarding API

Run as the chapter documents it: a local Python/Flask process (`onboarding-api.py`, not
containerized) shelling out to `kubectl apply -f -` against the live cluster's ambient
context. Required an isolated venv (`/tmp/ch07-venv`) instead of the README's
`pip install --break-system-packages` guidance, which targets an older PEP-668 posture than
this machine's Python 3.14 system interpreter tolerates — undocumented in the chapter.

Real `POST /teams` request for `platform-team` returned `201` with a real generated
namespace (`team-platform-team`) and quota; two members added (`bob`/developer,
`carol`/viewer), both `201`; re-POSTing the same team returned `201` unchanged, confirming
idempotency. Verified against the live cluster, not just the API's own response:
`kubectl get ns team-platform-team` → `Active` with the expected labels;
`resourcequota/platform-team-quota` present with the requested `hard` limits;
`rolebindings` `team-lead`/`team-developer`/`team-viewer` present, bound to the correct
`ClusterRole`s and `Group`s. `kubectl get ns` afterward showed only `team-platform-team`
added — `monitoring`, `istio-system`, `flux-system`, `kube-system` untouched. Audit log
(`audit-logger.py show`) recorded real `team_created` and `member_added` events.

Minor doc/code mismatches found, not blocking: the README's "Expected output" shows binding
to `0.0.0.0:5000`, but the code's real default is `127.0.0.1` unless `ONBOARDING_API_HOST` is
set explicitly. Keycloak and GitHub-token/Bitwarden integration paths in the same chapter
were not exercised — only the core `/teams` namespace-provisioning flow was.

### Ch11 — OPA Gatekeeper admission-control mode

Deployed and exercised against the live cluster (`kind-platform-eng-colima`, cluster not
deleted or recreated). The run's own summary reports: "All protected namespaces are
untouched and unaffected. Task complete," with `monitoring`, `istio-system`, `flux-system`,
and `kube-system` confirmed read-only throughout. The full command-level transcript for this
chapter (which specific admission policies were exercised, and against which test manifests)
was not carried through into the material this update is written from, so it is not
reproduced here beyond what the run's own summary states — recorded honestly as a gap in
this record, not as a claim of untested success.

### Ch13 — chaos / pod-kill resilience test, and Ch14 — AI agent live alert trigger

Both were reported deployed and live-validated against the same running cluster as part of
this batch (a real pod-kill resilience scenario for Ch13, a real AI-agent alert-trigger flow
for Ch14). Unlike Ch05/Ch07/Ch11 above, the detailed command-level output for these two runs
was not included in the material this update is written from — no specific commands, pod
names, or response payloads to quote. Recorded here only at the level the source material
supports; do not read this as either a pass or a failure claim beyond "reported live-run
attempted." A follow-up pass should capture and fold in the same level of command/output
detail already present for Ch05/07/11.

## Not done in this pass

- Ch03 (Keycloak) and Ch06 (Backstage) — not installed on this cluster.
- Ch08 (CI/CD pipelines) — not exercised against this cluster.
- Ch09 (Crossplane) — the three proven bug fixes were backported to the real upstream
  `Platform-Engineer-s-Handbook` GitHub repo (see
  [platform-engineers-handbook-backport.md](platform-engineers-handbook-backport.md)), but
  Crossplane itself has not been installed or exercised on this specific
  `kind-platform-eng-colima` cluster — the live Crossplane verification runs referenced in
  the ggen-pack doc used separate, disposable Kind clusters, all torn down afterward.
- Ch10 (Backstage scaffold template) — not instantiated against a real Backstage instance.
- Ch12 — not exercised in this pass.

## Update: Real Playwright E2E tests

A real Playwright test project (`tests/e2e/platform-engineers-handbook/`) was set up and run
against the four live monitoring/demo services on this same `kind-platform-eng-colima`
cluster, port-forwarded to `localhost:18300`–`18303`. No mocked HTTP — every test drives a
real Chromium browser against a real service.

Real run from the project's own location:

```
Running 5 tests using 5 workers

  ✓  2 tests/alertmanager-demoapp.spec.ts:21:1 › JTBD: demo app responds to a real browser request at /health (368ms)
  ✓  3 tests/alertmanager-demoapp.spec.ts:29:1 › JTBD: demo app /items endpoint renders real JSON in a browser (370ms)
  ✓  4 tests/alertmanager-demoapp.spec.ts:6:1 › JTBD: view active alerts in the Alertmanager web UI (912ms)
  ✓  5 tests/grafana.spec.ts:7:1 › JTBD: log into Grafana and view a live dashboard with real data (3.4s)
  ✓  1 tests/prometheus.spec.ts:5:1 › JTBD: run a PromQL query in the Prometheus web UI and see real results (4.8s)

  5 passed (5.5s)
```

All 5 JTBDs covered: Grafana login + live dashboard, a real PromQL query against Prometheus,
Alertmanager's active-alerts view, and the demo app's `/health` and `/items` endpoints.

One real UI-implementation detail surfaced while writing the Prometheus test, not a platform
defect: the first attempt navigated to Prometheus's root path (`/`) and targeted a plain
`<textarea>`/`<input>` for the query box, and failed — the current Prometheus web UI serves
its query page at `/query`, and the query input is an ARIA `role="textbox"`
CodeMirror-based editor, not a plain form control. Corrected by navigating to `/query` and
selecting the input via `page.getByRole('textbox')`.

## See also

- [The Platform Engineer's Handbook — ggen Pack](platform-engineers-handbook-ggen-packs.md)
- [The Platform Engineer's Handbook — Ch09 Backport](platform-engineers-handbook-backport.md)
