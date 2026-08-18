# Data Residency

Last updated: 2026-08-18

This document answers, directly and in procurement/legal language, the question
`docs/SCOPE-AND-LIMITATIONS.md` and `docs/DISASTER-RECOVERY.md` answer only indirectly for an
engineering reader: **where does data on this platform physically live, and what data-locality
guarantee does that give you?** It is a restatement of facts already established elsewhere in
this repository, not a new claim — see "Source of every fact in this document" at the end for
the exact citation behind each line.

## Answer, in one sentence

All data on this platform — every database row, every object-storage file, every audit-log
entry, every secret — is stored on a single physical machine, at a single physical location,
with **no replication to any other machine, datacenter, availability zone, or region**. There
is no data-sovereignty or data-locality guarantee beyond "wherever that one machine currently
is."

## Where, concretely

| Layer | What it is | Where it physically resides today |
|---|---|---|
| Physical host | The machine running Docker/colima | One physical machine (Apple Silicon, `arm64`) running macOS, under a single operator's control. Not a cloud region, not a managed hosting facility. |
| Virtualization | `colima` (macOS Virtualization.Framework) | A single Linux VM inside that same physical machine — `colima status` reports `arch: aarch64`, `mountType: virtiofs`, backed by that host's own local disk. |
| Kubernetes cluster | `kind-platform-eng-colima`, single-node `kind` cluster | Runs entirely inside that one colima VM. `kubectl get nodes` returns exactly one node, `platform-eng-colima-control-plane` — see `docs/SCOPE-AND-LIMITATIONS.md` §1. There is no second node, in this location or any other, for any object to be replicated to. |
| Postgres rows (project databases, `platform_console.audit_log`, `platform_console.active_sessions`) | Data written through `/projects`, `/audit`, `/sessions`, and every project's Postgres | A single-replica `StatefulSet` Pod per project, backed by a `PersistentVolumeClaim` on the cluster's default `standard` StorageClass (`rancher.io/local-path` provisioner — confirmed via `kubectl get sc`). `local-path` provisions volumes as directories on the node's own local disk — i.e., on that same one physical machine, not network-attached or cloud block storage. |
| Object storage (project Storage buckets, backup dumps) | Supabase Storage service data, `pg_dump` output on `platform-backups-pvc` | Same mechanism as above: a `local-path`-provisioned PVC, a directory on the single node's local disk. `kubectl get pvc -A` shows every project PVC (`demo-db-postgres-data`, `demo-project-storage-data`, `demo-project-studio-data`, `platform-backups-pvc`) bound this way. |
| Audit logs | `platform_console.audit_log` table (durable) plus stdout (ephemeral) | The durable copy is Postgres rows on the same single-node local-path storage as above (README's `/audit` module description). The stdout copy is container log data captured by the container runtime on that same node and is lost on pod restart — never shipped off-host. |
| Secrets (API keys, DB credentials, session-signing key, webhook secrets) | Kubernetes `Secret` objects | Stored in this single-node cluster's own `etcd`, which itself lives on the same node's local disk (no separate etcd cluster, no KMS-backed envelope encryption configured — `kind`'s default etcd storage is unencrypted at rest). No secret is replicated, backed up externally, or synced to any secrets-management service outside this cluster. |
| Git history (source code, this doc, the evidence bundle) | This repository | Wherever this repo's remote is hosted — outside the scope of "production data" above, called out here only so it isn't confused with the runtime data rows in this table. |

## What this means for data-sovereignty and cross-border rules

- **No multi-region replication of any kind.** There is one copy of every row, one copy of
  every object-storage file, one copy of every secret. Nothing is written to two places.
- **No region selection.** There is no mechanism — API, console setting, or configuration file
  — anywhere in this codebase that lets a user or admin choose which region or jurisdiction
  their project's data lands in. All projects land on the same single node, because there is
  only one node.
- **No data-locality guarantee of any kind can be made today.** If asked "can you guarantee EU
  customer data stays in the EU" / "can you guarantee this data never crosses a border" / "can
  you keep Sony content data segregated from other tenants' physical storage" — the honest
  answer is **no**, because every tenant's data already shares the same single disk, the same
  single node, the same single physical machine, with no mechanism to constrain or attest to
  where that machine is.
- **Backups do not change this.** The Database Backups module (`/projects/[name]/backups`,
  documented in the README and `docs/DISASTER-RECOVERY.md`) writes `pg_dump` output to
  `platform-backups-pvc` — a PVC on the same single node's local disk, not a second location.
  A disk failure on that one machine can take the live data and its on-cluster backups down
  together; see `docs/DISASTER-RECOVERY.md` for the real incident where exactly that class of
  failure happened (etcd storage corruption, no snapshot existed at the time).
- **Encryption at rest is not currently configured.** `kind`'s default etcd storage has no KMS
  provider configured, so Kubernetes `Secret` objects are stored unencrypted at the etcd layer
  (base64-encoded, not encrypted) — the same as any unmodified `kind`/`kubeadm` cluster's
  out-of-the-box default. This is a real, disclosed gap, not an assumption; no claim is made
  here that encryption-at-rest exists where it does not.

## What would be required to add a real region guarantee

None of the following exists today. Listed so a reviewer can see the concrete gap between
"where data lives now" and "what a real regional-guarantee claim would require":

1. **A managed, multi-node, multi-AZ Kubernetes control plane** (EKS/GKE/AKS, or a
   self-managed 3/5-node etcd cluster spanning real failure domains) — replacing the current
   single-node `kind` cluster described in `docs/SCOPE-AND-LIMITATIONS.md` §1.
2. **Network-attached, region-pinned block/object storage** (e.g. EBS/Persistent Disk/Managed
   Disk, or a real object store like S3/GCS/Blob Storage with a bucket region setting) —
   replacing the current `rancher.io/local-path` provisioner, which is defined specifically to
   bind storage to whichever single node the Pod lands on.
3. **A region-selection mechanism in the provisioning API** (`/projects`'s create flow) that
   actually pins a new project's Postgres/Storage to infrastructure in a chosen region, plus a
   real inventory of which regions exist to choose from.
4. **KMS-backed encryption at rest** for `Secret` objects and PVC-backed volumes, with the key
   material itself under a documented residency policy (a KMS key is also data with a
   location).
5. **A documented sub-processor / hosting-facility list** naming the actual legal entity and
   physical/cloud location(s) data would reside in — meaningful only once (1)-(3) exist; today
   the honest sub-processor answer is "the operator's own physical machine," not a named
   facility.
6. **A contractual data-processing agreement (DPA)** covering the above, which requires the
   infrastructure commitments above to exist first — a DPA cannot promise a residency this
   platform's architecture cannot enforce.

Building any of the above is out of scope for this document; it exists to state the gap
plainly, not to close it.

## Source of every fact in this document

- Single-node cluster, single physical machine: `docs/SCOPE-AND-LIMITATIONS.md` §§1-2, and this
  session's own `kubectl get nodes -o wide` (one node,
  `platform-eng-colima-control-plane`, `Ready`).
- `local-path` / node-local PVC storage: this session's own `kubectl get sc` (`standard
  (default)`, provisioner `rancher.io/local-path`, `VOLUMEBINDINGMODE: WaitForFirstConsumer`)
  and `kubectl get pvc -A` (every project PVC bound this way).
- colima VM on a physical macOS host: this session's own `colima status` (`macOS
  Virtualization.Framework`, `arch: aarch64`).
- No backup mechanism existed at the time of the original etcd loss, and the mechanism that
  exists today still writes to the same single node: `docs/DISASTER-RECOVERY.md` §§1, 3, 4.
- Audit log durability model (Postgres row durable, stdout ephemeral): README's `/audit` module
  description and `evidence/control-evidence-bundle.json`'s
  `audit-log-durable-and-queryable` control.
- Secrets stored as k8s `Secret` objects, unencrypted at etcd's default: `kind`'s documented
  default behavior (no KMS provider configured in `infra/kind-config.yaml`); consistent with
  the plaintext-credential-discovery pattern the README documents for the Backups/Audit modules
  (`getSecretValue`, `getPostgresConnectionInfo` in `lib/k8s.ts`).

## See also

- `README.md` — "What 'PaaS' concretely means here" (the top-level disclaimer this document
  narrows to the residency question specifically)
- `docs/SCOPE-AND-LIMITATIONS.md` — the full honest-scope statement this document's storage
  facts are drawn from (§§1-3 in particular)
- `docs/DISASTER-RECOVERY.md` — the real incident and runbook demonstrating what "single
  machine, no replication" meant in practice
- `evidence/control-evidence-bundle.json` — the `data-residency-statement-published` control
  entry for this document
