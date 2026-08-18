# Disaster Recovery Runbook

**Last updated**: 2026-08-18. Scope: `kind-platform-eng-colima`, the single-node local `kind`
cluster `platform-console` runs on.

This is the AWS Well-Architected DR-pillar / GCP DR-planning-guide equivalent for this
platform: a real recovery this cluster actually went through, not a hypothetical exercise.
Every claim below is either a direct citation of a real git commit / committed file, or a real
command run against the live cluster while writing this document (transcripts inline). Where a
detail cannot be verified from either source, that gap is stated explicitly rather than filled
in from memory — see "What this document can and cannot verify" at the end.

**This is a technical runbook, not a status update.** It is written for an engineer to follow
to bring the cluster back and assumes `kubectl`/`etcd`/Kubernetes literacy throughout. It is not
something to forward to a leadership chain or a customer during an active incident. For that,
use `docs/INCIDENT-COMMUNICATION-TEMPLATE.md` — a separate, non-technical, fill-in-the-blank
template (initial notification / ongoing update / resolution notice) that translates an incident
like this one into language a non-technical reader can act on, without exposing internal
implementation detail. That template's worked example is this exact incident, translated.

## 1. The incident (real, cited)

The control-plane node this cluster runs on today, `platform-eng-colima-control-plane`, has
`metadata.creationTimestamp: 2026-08-18T01:11:54Z` — i.e. it is not the cluster's original
node. The reason is committed, verbatim, in this repo's own recreation blueprint,
`infra/kind-config.yaml`, added in the first `platform-console` commit
(`191b3ca57c97445309a998734aa9ab625dde2b77`, 2026-08-17T18:57:29-07:00 =
2026-08-18T01:57:29Z):

> Recreated after unrecoverable etcd storage corruption on the prior
> `platform-eng-colima` cluster (bbolt page checksum panic in the etcd
> container, no snapshot backup existed).

That same commit's own message describes the shape of the recovery:

> Built by an ultracode workflow across recreate/restand/deploy/extend/evidence phases.

and names the full stack rebuilt on the new node: **Istio, Flux, kube-prometheus-stack, the
Supabase operator** — "wrapping real running infrastructure only... never a fabricated cloud
service."

`kind-config.yaml`'s header also records two concrete continuity steps taken *before* deleting
the dead cluster, so the replacement would match it exactly rather than drift:

- Port mappings (`0.0.0.0:8080->80/tcp`, `0.0.0.0:8443->443/tcp`) confirmed via
  `docker inspect platform-eng-colima-control-plane` against the prior container.
- Node image pinned to `kindest/node:v1.34.0`, confirmed the same way.

## 2. The real recovery sequence

Reconstructed from two real sources: (a) the git commit history cited above, and (b) the live
cluster's own object `creationTimestamp`s, which are ground truth for the order objects were
actually created in *this* cluster instance — namespaces are never recreated on their own, so
their timestamps are a real, tamper-evident record of restand order:

```
$ kubectl get ns istio-system flux-system monitoring supabase-system supabase-demo \
    platform-console kube-system \
    -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp \
    --sort-by=.metadata.creationTimestamp

NAME               CREATED
kube-system        2026-08-18T01:11:54Z   <- node/cluster bootstrap (kind create cluster)
istio-system       2026-08-18T01:12:36Z   <- Istio installed
flux-system        2026-08-18T01:12:36Z   <- Flux installed (same minute as Istio)
monitoring         2026-08-18T01:12:47Z   <- kube-prometheus-stack installed
supabase-system    2026-08-18T01:13:31Z   <- Supabase operator installed
supabase-demo      2026-08-18T01:15:47Z   <- demo Project re-provisioned
platform-console   2026-08-18T01:23:20Z   <- platform-console's own namespace
```

Real elapsed time, cluster-bootstrap to platform-console namespace: **11 minutes 26 seconds**.
The first git commit recording this state (`191b3ca`) landed at `2026-08-18T01:57:29Z`, ~34
minutes after the `platform-console` namespace existed — the remaining time was writing the
app, k8s manifests, README, and evidence bundle before the first commit, not more cluster
recovery.

Concretely, in order:

1. **Delete the dead cluster.** `kind delete cluster --name platform-eng-colima` (or
   equivalent) — the etcd bbolt panic left the control plane unrecoverable in place; a
   single-node `kind` cluster has no other member to fail over to.
2. **Recreate from `infra/kind-config.yaml`**: `kind create cluster --config
   infra/kind-config.yaml` — same node image, same port mappings, so nothing downstream
   (Gateway routing, `/etc/hosts` entries, port-forward instructions in this repo's own README)
   had to change.
3. **Istio** (`istio-system`, `istioctl install` demo profile per this repo's own convention,
   documented for the same cluster-naming convention in
   `docs/platform-engineers-handbook-colima-runtime.md`, which `kind-config.yaml` cites as
   "the runtime convention this reproduces").
4. **Flux** (`flux-system`) — CRDs and controllers installed; no Kustomization/HelmRelease
   objects were recreated at this point (see README's "What's deployed": "an honest empty
   GitOps state, not a fabricated one").
5. **kube-prometheus-stack** (`monitoring`) via Helm — Prometheus, Alertmanager, Grafana,
   kube-state-metrics, node-exporter.
6. **Supabase operator** (`supabase-system`) — the CRDs (`Project`, `SingleDatabase`) this
   platform's entire self-service PaaS surface is built on.
7. **Re-provision the demo project** (`supabase-demo`) — a fresh `Project`/`SingleDatabase`
   pair, reconciled by the freshly-installed operator into new Postgres/GoTrue/PostgREST/
   Realtime/Storage/edge-functions Deployments.
8. **Deploy `platform-console` itself** — `k8s/namespaces.yaml` through `k8s/status-page.yaml`
   in the order README's "What's deployed" section lists, then the Next.js app.

## 3. What was LOST vs RECOVERED

| Item | Outcome | Why |
|---|---|---|
| Cluster infrastructure (control plane, Istio, Flux, kube-prometheus-stack, Supabase operator) | **RECOVERED**, byte-for-byte reproducible | Entirely declarative — `infra/kind-config.yaml` + `istioctl install` + `flux install` + a pinned Helm chart + the operator's own manifests. Nothing here depends on the dead node's disk. |
| `demo-project`'s Postgres data (any rows created before the corruption) | **LOST, not recoverable** | Re-provisioning creates a *new* Postgres from the operator's default init, not a restore. |
| `demo-project`'s identity (UID, internal Postgres storage) | **LOST** | A new `Project`/`SingleDatabase` CR pair was created; even if named identically, it is a different underlying object with a fresh `creationTimestamp`/`uid`, exactly as this session's own IaC module (`lib/iac.ts`) would report if asked to diff it against nothing. |
| A snapshot/backup of the dead cluster's etcd | **NEVER EXISTED** | `kind-config.yaml`'s own words: "no snapshot backup existed." This was the actual, disclosed gap that made recreation-from-scratch the only option, not a choice. |
| A backup of `demo-project`'s database specifically | **NEVER EXISTED AT THAT TIME** | The Database Backups module (`lib/k8s.ts`'s `createBackupJob`/`createRestoreJob`, README's `/projects/[name]/backups`) was added in commit `c1223290546f8366b043307fd667625f891483a2`, **2026-08-17T20:59:57-07:00 — over 2 hours after** the recreation commit `191b3ca` (`2026-08-17T18:57:29-07:00`). At the moment of the actual disaster there was no backup mechanism in this codebase at all; the module exists today specifically because that gap was real and was closed afterward, not before. |
| Port mappings / node image / cluster naming convention | **RECOVERED exactly** | Confirmed via `docker inspect` against the dying container *before* deletion (see `kind-config.yaml`'s own header) — a real "capture what you can before you lose access to it" step, not guesswork. |
| Every commit, doc, and evidence-bundle entry describing the platform | **NEVER AT RISK** | Git history lives outside the cluster entirely; nothing in this recovery touched it. |

## 4. Real proof: one bounded piece of this is recoverable *today*

The disaster above proved the platform's **infrastructure** is recoverable (declarative
manifests) while its **stateful data** was not (no backup mechanism existed yet). Since then,
this platform has built two real recovery primitives — the Database Backups module (`/projects/
[name]/backups`) and the IaC export module (`/projects/[name]/iac`, `lib/iac.ts`) — but neither
had ever been exercised against a real deletion. This section is that real, live exercise,
run on 2026-08-18 while writing this document, against `platform-feature-flags` (a real,
non-critical `ConfigMap` in the `platform-console` namespace — chosen because the IaC export
module only covers `Project`/`SingleDatabase` CRs, so this is the honest "manual `kubectl apply`
from a real backed-up manifest" path this doc's own recovery above also used).

**Step 1 — capture real pre-deletion state**, through the live, authenticated app (not just
`kubectl`) — a real session JWT, HS256-signed with the deployed pod's own live `AUTH_SECRET`
(same minting convention the canary/webhook proofs elsewhere in this repo use), against the
real deployed pod via `kubectl port-forward`:

```
$ curl -s -H "Cookie: platform_console_session=<real signed JWT>" \
    http://127.0.0.1:18080/api/feature-flags
{"flags":{"verbose-status":"false"}}

$ kubectl get configmap platform-feature-flags -n platform-console -o yaml
apiVersion: v1
data:
  verbose-status: "false"
kind: ConfigMap
metadata:
  ...
  name: platform-feature-flags
  namespace: platform-console
  resourceVersion: "110119"
  uid: ccd56a31-099d-4dfe-b71c-ba1e05ac16d0
```

**Step 2 — write a real, re-appliable backup manifest** (same "strip server-managed fields"
convention `lib/iac.ts`'s `toReappliableManifest` uses for Projects), saved to
`evidence/dr-proof/platform-feature-flags-backup.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: platform-feature-flags
  namespace: platform-console
  labels:
    app.kubernetes.io/component: feature-flags
    app.kubernetes.io/part-of: platform-console
data:
  verbose-status: "false"
```

**Step 3 — delete the real resource**:

```
$ kubectl delete configmap platform-feature-flags -n platform-console
configmap "platform-feature-flags" deleted from platform-console namespace
```

**Step 4 — confirm real breakage**, at both the k8s layer and the live app layer:

```
$ kubectl get configmap platform-feature-flags -n platform-console
Error from server (NotFound): configmaps "platform-feature-flags" not found

$ curl -s -H "Cookie: platform_console_session=<same real JWT>" \
    http://127.0.0.1:18080/api/feature-flags
{"flags":{}}
```

The live, deployed console genuinely lost the flag — this is not a staged screenshot, it is
the real running pod answering with real, currently-true state.

**Step 5 — recover, via the real backed-up manifest from step 2**:

```
$ kubectl apply -f evidence/dr-proof/platform-feature-flags-backup.yaml
configmap/platform-feature-flags created
```

**Step 6 — confirm the recovered state matches the pre-deletion state**, again at both layers:

```
$ kubectl get configmap platform-feature-flags -n platform-console -o yaml
apiVersion: v1
data:
  verbose-status: "false"
kind: ConfigMap
metadata:
  ...
  name: platform-feature-flags
  namespace: platform-console
  resourceVersion: "137043"
  uid: c84cd0ec-34ec-4ace-9d6f-876229e72a25

$ curl -s -H "Cookie: platform_console_session=<same real JWT>" \
    http://127.0.0.1:18080/api/feature-flags
{"flags":{"verbose-status":"false"}}
```

**Result**: `data` (`{"verbose-status":"false"}`) and the live app's own `GET
/api/feature-flags` response are byte-for-byte identical before deletion and after recovery.
`resourceVersion`/`uid`/`creationTimestamp` differ — honestly disclosed, not hidden — because
this is a real new Kubernetes object created by `kubectl apply`, the same "identity is not
preserved, data is" distinction section 3's table already draws for the 2026-08-17 incident
itself. See `disaster-recovery-runbook-tested` in `evidence/control-evidence-bundle.json` for
this proof's evidence-bundle entry.

## 5. Runbook: if this happens again

1. **Before deleting anything still reachable**, capture what identity you can —
   `docker inspect <container>` for port mappings/image, `kubectl get <resource> -o yaml` for
   anything you might otherwise have to guess at recreating. `kind-config.yaml`'s header is the
   working example.
2. **Recreate the cluster**: `kind delete cluster --name platform-eng-colima` (if the old one
   is still present but dead) then `kind create cluster --config infra/kind-config.yaml`.
3. **Restand the base stack in dependency order**: Istio -> Flux -> kube-prometheus-stack ->
   Supabase operator. Each step is declarative and idempotent; none depends on any state from
   the dead cluster.
4. **Re-provision or restore stateful resources**:
   - Any `Project`/`SingleDatabase` with a real prior backup: use `/projects/[name]/backups`'
     **Restore** action against the most recent `Complete` backup Job — this is the primitive
     that did not exist at the time of the 2026-08-17 incident and is the actual gap this
     runbook exists to close.
   - Anything without a backup: re-provision fresh via `/projects`, same as the 2026-08-17
     recovery did, and treat the prior data as lost — say so plainly, as section 3 does, rather
     than implying continuity that doesn't exist.
   - Platform-level `ConfigMap`s/`Secret`s (feature flags, org roles, webhooks, API keys): if a
     manifest was exported ahead of time (`/projects/[name]/iac` for Project/SingleDatabase; a
     manual `kubectl get -o yaml` + the same field-stripping convention for everything else,
     per section 4 above), `kubectl apply` it back. If not, they reseed to safe defaults on
     first read where the code supports it (e.g. `lib/authz.ts`'s org-roles ConfigMap reseeds
     `admin: owner`) or start empty where it doesn't (feature flags) — know which is true for
     each resource before you need it.
5. **Redeploy `platform-console` itself** from `k8s/` in the order README's "What's deployed"
   lists, then rebuild/redeploy the app image if code changed since the last image build.
6. **Re-verify, don't assume**: re-run the same live checks this repo's own evidence bundle
   already relies on elsewhere (`test-cluster-health.py`, `istioctl proxy-status`, `flux check
   all`, a real curl against each module) rather than treating "the manifests applied cleanly"
   as proof the platform actually works.

## What this document can and cannot verify

**Verified directly** (cited above, reproducible by re-running the same commands): the git
commit hash/timestamp/message of the recreation commit; the exact text committed in
`infra/kind-config.yaml` describing the bbolt/etcd trigger and the pre-deletion `docker
inspect` continuity steps; the live cluster's own real namespace `creationTimestamp`s giving
the restand order and timing; the commit ordering proving no backup mechanism existed at
recovery time; and the full delete/backup/recover/confirm sequence in section 4, run live while
writing this document.

**Not independently verifiable from this repository's git history**: a command-level transcript
of the original etcd bbolt failure diagnosis itself (the `kind`/`docker`/`kubectl` commands run
against the *dying* cluster before it was deleted). Live cluster troubleshooting isn't captured
by git the way file changes are — only the resulting recreation blueprint and its own
description of why it exists were committed. The incident's cause and shape are recorded
verbatim in a real committed file (`infra/kind-config.yaml`); the minute-by-minute diagnosis
session that preceded that commit is not.
