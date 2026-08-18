# Scope and Limitations

Last updated: 2026-08-18

This document is the honest counterpart to the module table in `README.md`. Every module
listed there is real -- real Kubernetes objects, real API calls, real live-verified behavior,
each backed by an entry in `evidence/control-evidence-bundle.json`. That reality claim is
narrow, though: it is about the *mechanism* (each control genuinely does what it says on this
cluster), not about *scale*. This document names, plainly, what the platform does NOT provide
despite 40 modules claiming feature parity with GCP/AWS/Azure PaaS surfaces, and which specific
module's language could be misread as a broader claim than it makes.

The rule applied throughout: every limitation below names the exact module whose claims could
be over-read, and states the precise honest scope right next to it -- the same per-control
discipline `evidence/control-evidence-bundle.json` already applies, extended here to the
platform's overall claims.

## 1. Single control-plane node -- no real HA/failover

**The claim that could be misread**: `/iam`, `/network`, and `/topology` describe real RBAC,
real NetworkPolicy enforcement, and a real cluster topology -- language that, read out of
context, sounds like it describes a production control plane with redundancy.

**The honest scope**: `kind-platform-eng-colima` is a **single-node** cluster
(`kubectl get nodes` returns exactly one: `platform-eng-colima-control-plane`, `Ready`,
`control-plane` role). There is no etcd quorum, no second API server, no kubelet failover, no
real leader election across machines. If `platform-eng-colima-control-plane` dies -- the
underlying VM crashes, the disk fills, colima itself is torn down -- every module on this
console, the API server, etcd, and every workload in every namespace goes down with it, all at
once, with no automatic recovery. `docs/DISASTER-RECOVERY.md` documents exactly this failure
mode already happening once (an unrecoverable etcd bbolt page-checksum panic) and the manual,
from-scratch recreation it took to come back. A real multi-AZ control plane (EKS/GKE/AKS
managed control planes, or a self-managed 3/5-node etcd cluster) tolerates losing one node
without an outage; this platform cannot, by construction, because there is only one node to
lose.

## 2. Single physical machine -- no real multi-region, no real network partition tolerance

**The claim that could be misread**: `/network`'s Pod CIDR, Service CIDR, and mTLS
reachability-matrix data is described as "real Network Topology (AWS VPC console / GCP VPC
Network Topology / Azure Virtual Network diagram equivalent)."

**The honest scope**: `/network` describes **this cluster's internal pod/service networking
on one physical machine** -- `10.244.0.0/24` (kubeadm's single-node pod CIDR) and
`10.96.0.0/16` (the observed Service CIDR), both entirely inside one host's network namespace
via CNI, not a real routed VPC spanning availability zones or regions. There is no real
multi-region backbone, no real cross-AZ latency, no real network-partition scenario to tolerate
-- every "network path" the reachability matrix reports is a virtual interface hop on the same
kernel. The equivalence to "AWS VPC console" is a **shape** claim (a console showing you your
network topology), not a claim that this is a real multi-region VPC with the failure
characteristics one implies.

## 3. Single Postgres instance per project -- no read replicas, no real point-in-time recovery

**The claim that could be misread**: `/projects/[name]/backups` is described as "Database
Backups (RDS/Cloud SQL/Cloud Spanner automated-backup equivalent)" with a "Restore" action
described as "the RDS/Cloud SQL point-in-time-restore equivalent."

**The honest scope**: every project's Postgres is a **single StatefulSet Pod**, one replica,
with a single PVC. There is no streaming replication, no standby, no read replica to fail over
to or to serve read traffic from -- if that one Pod's PVC is corrupted or lost outside of a
snapshot window, the data between the last backup and the incident is gone. "Point-in-time
recovery" in the RDS/Cloud SQL sense means continuous WAL archiving letting you restore to any
second in the last N days; this platform has **on-demand `pg_dump` snapshots only**, taken when
a user clicks "Run backup now" (or via a `CronJob`, if scheduled through `/scheduled-jobs`) --
recovery granularity is exactly the gap between backups, not continuous. The README already
discloses a real, observed restore defect (FK-order dependent rows can land unrestored in the
same pass) -- that defect is itself evidence this is snapshot-and-replay, not a managed
continuous-recovery service.

## 4. No real customer-facing SLA

**The claim that could be misread**: `/status` is described as a "Public Status Page (AWS
Service Health Dashboard / statuspage.io equivalent)" showing "a real computed uptime%."

**The honest scope**: the uptime percentage on `/status` is real -- it is genuinely computed
`avg_over_time(up{...}[1h])`-style PromQL against the real in-cluster Prometheus, not a static
"all systems operational" placeholder, and the README documents a real induced-outage proof of
that. What it is not: an SLA. An SLA is a contractual promise **about** a service, backed by
credits or penalties, made by an operator to a customer. This page **reports** uptime
**observed from** this single-node cluster; it makes no promise about future uptime, offers no
remedy for downtime, and has no counterparty -- there is no customer relationship for a status
page to be an SLA toward. The 99.9%/99.99%-style numbers that accompany real hyperscaler status
pages are commitments; this platform's number is a measurement only.

## 5. Local kind cluster networking -- mesh is real, but single-node

**The claim that could be misread**: `/network`'s mTLS section describes "the real Istio mTLS
trust boundary" as STRICT-enforced, and `/topology`/`/iam` describe NetworkPolicy enforcement
as real and live-verified (three throwaway curl pods, matching the matrix's claims exactly).

**The honest scope**: the enforcement is genuinely real -- STRICT `PeerAuthentication` objects
are real Istio CRs, actually blocking cross-namespace traffic that the reachability matrix
says should be denied (live-verified with real `curl: (28) Connection timed out` results, not
policy-object existence alone). What that enforcement describes is a **single-node service
mesh**: every sidecar proxy, every mTLS handshake, every NetworkPolicy-enforced drop happens
inside one Linux kernel's network namespace on one machine. There is no real multi-region mesh
control plane, no cross-region mTLS certificate distribution, no real network-partition
scenario between mesh members -- because there is only one node for every member to run on.
The mechanism (mTLS handshake, policy enforcement) is identical to what a multi-region mesh
does; the topology it operates over is not.

## Summary table

| Module(s) | What's real | What's NOT provided |
|---|---|---|
| `/iam`, `/network`, `/topology`, cluster-wide | Real single-node RBAC/NetworkPolicy/topology, live-verified | No multi-node HA, no failover if the one control-plane node dies |
| `/network` | Real pod/service CIDR and reachability matrix for this host | No multi-region VPC, no real network-partition tolerance |
| `/projects/[name]/backups` | Real on-demand `pg_dump` snapshots + restore, one Postgres Pod per project | No streaming replicas, no continuous point-in-time recovery |
| `/status` | Real computed uptime from live Prometheus data | No contractual SLA, no customer relationship, no remedy for downtime |
| `/network` (mTLS), Istio mesh cluster-wide | Real STRICT mTLS, real enforcement, live-verified | Single-node mesh only, no multi-region mesh control plane |

## See also

- `README.md` -- "What 'PaaS' concretely means here" (the top-level disclaimer this document
  expands on)
- `docs/DISASTER-RECOVERY.md` -- the real incident and runbook behind limitation #1
- `evidence/control-evidence-bundle.json` -- per-control evidence and disclaimer; the
  `platform_scope_and_limitations` top-level field points back to this document
