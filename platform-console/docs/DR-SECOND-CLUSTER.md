# Second Cluster: Cold-Standby DR Target

Updated 2026-08-18.

## What exists

A second, independent local `kind` cluster, `kind-platform-eng-colima-dr`,
running alongside the existing `kind-platform-eng-colima` cluster on the same
Mac. It was created with `kind create cluster --name platform-eng-colima-dr`
and does not share nodes, control plane, storage, or networking with the
primary cluster.

A script, `platform-console/scripts/dr-export-apply.sh`, exports the live
resource manifests (Deployments, Services, ConfigMaps, Secrets,
ServiceAccounts, Roles/RoleBindings, HPAs) of the `platform-console`
namespace from the primary cluster and applies them to the DR cluster. It
excludes the two Kubernetes-auto-managed objects (`kube-root-ca.crt`
ConfigMap, `default` ServiceAccount) that every namespace gets from its own
cluster's control plane, to avoid a resourceVersion conflict.

Verified 2026-08-18: running the script produced a clean apply
(`namespace/platform-console created`, all listed Deployments / Services /
ConfigMaps / Secrets / RBAC / HPA `created`), and
`kubectl --context kind-platform-eng-colima-dr get all -n platform-console`
showed the three Deployments (`platform-console-gateway`,
`platform-console-oidc-idp`, `platform-prober`) and their Services and
ReplicaSets present and scheduling. The primary cluster was re-checked
immediately after and showed zero non-`Running`/`Completed` pods (5
`Completed`, 40 `Running`), confirming it was not touched.

## What this does NOT provide

- **Not HA.** There is no automatic failover between the two clusters. If the
  primary cluster or the single Mac it runs on goes down, nothing switches
  traffic to the DR cluster automatically.
- **Not multi-region.** Both clusters run as `kind` (Docker-in-Docker)
  clusters on the same physical machine. There is no second region, no
  second machine, no independent power/network domain.
- **Not live replication.** The DR cluster's copy of `platform-console` is a
  point-in-time snapshot taken at the moment `dr-export-apply.sh` is run. Any
  writes to the primary's databases, in-memory state, or subsequent config
  changes after that moment are not reflected on the DR cluster until the
  script is run again.
- **No customer SLA change.** This does not alter the "single-node,
  single-machine, no HA, no multi-region, no customer SLA" status of the
  platform. That flag on the honesty slide remains accurate and should stay
  flagged as an open gap.
- **No data-tier replication.** The script exports Kubernetes resource
  manifests only. It does not export or replicate any persistent volume data,
  database contents, or external state.

## What this is an honest first step toward

A second, independently-provisioned cluster that can receive a cold copy of
the platform's manifests on demand. Extending this into real DR/HA would
require, at minimum: the DR cluster running on separate physical
infrastructure (not the same Mac), automated/scheduled export-apply (not a
manually-run script), real data-tier replication, and a tested failover
procedure with health-check-driven traffic cutover — none of which exist yet.

## How to run it

```bash
./scripts/dr-export-apply.sh
```

Env vars `PRIMARY_CONTEXT`, `DR_CONTEXT`, `NAMESPACE`, `OUT_DIR` override the
defaults (`kind-platform-eng-colima`, `kind-platform-eng-colima-dr`,
`platform-console`, `/tmp/platform-console-dr-export`).

## Tearing down the DR cluster

```bash
kind delete cluster --name platform-eng-colima-dr
```

This does not affect `kind-platform-eng-colima`.
