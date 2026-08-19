
# 01 — System description

The audited system's boundaries, infrastructure, and components — real
facts the consuming project supplies, never fabricated by this pack.

## Organization

**chatman-ecosystem**

Constitution-governed multi-service platform (platform-console PaaS, ggen generation engine, autofde-lab, gymact, and related services) operating under a 10-law CONSTITUTION.md (zero unreceipted actuation, broker-only DO, evidence-before-standing) and a 10-rule AGENTS.md agent operating law, enforced in CI by scripts/crown.sh.
**Kubernetes control plane images / official container base images (node:20-slim, node:22-slim, python:3.12-slim, python:3.13-slim, rustlang/rust:nightly-slim)**

_(no description supplied)_
**aquasec/trivy (Aqua Security open-source scanner) and its public vulnerability DB mirror (mirror.gcr.io/aquasec/trivy-db)**

_(no description supplied)_
**GitHub Actions marketplace actions (actions/checkout, dtolnay/rust-toolchain, Swatinem/rust-cache, taiki-e/install-action)**

_(no description supplied)_
**kind (Kubernetes-in-Docker) as the only real cluster substrate**

_(no description supplied)_
**kind / Kubernetes (self-managed, single-node, via colima)**

_(no description supplied)_
**Istio**

_(no description supplied)_
**Supabase (operator + Postgres/GoTrue/PostgREST/Realtime/Storage stack)**

_(no description supplied)_
**Prometheus / kube-prometheus-stack (via Helm) and Grafana**

_(no description supplied)_
**Flux**

_(no description supplied)_
**Cloud/Kubernetes cluster provider (unspecified, self-hosted per manifests)**

_(no description supplied)_
**Istio service mesh (istio-system namespace, istiod)**

_(no description supplied)_
**Kubernetes cluster (kind, single-node, self-hosted on 'kind-platform-eng-colima')**

_(no description supplied)_
**rustlang/rust:nightly-slim and python:3.12-slim (Docker Hub base images)**

_(no description supplied)_
**Docker Hub / OCI registry (implicit, image pull source for the above)**

_(no description supplied)_


## System boundaries

| Component | Notes |
|---|---|
| Single-node kind Kubernetes cluster (kind-platform-eng-colima) running platform-console | In scope: a single-node kind cluster (self-hosted via colima) running platform-console (PaaS console), the ggen generation engine (services/ggen), Istio service mesh (STRICT mTLS PeerAuthentication across autofde-lab, gymact, ggen, ggen-marketplace, platform-console namespaces), Prometheus/Grafana monitoring, Supabase-operator-managed per-project Postgres/GoTrue/PostgREST/Realtime/Storage, and Flux (installed, inactive GitOps state). No multi-node control plane, no cloud-managed Kubernetes (EKS/GKE/AKS), no HA etcd -- one control-plane node, one etcd, one API server, one kubelet, per docs/SCOPE-AND-LIMITATIONS.md and SONY-READINESS-GAP-CLOSURE.md. |


## How to supply these facts

```turtle
[] a org:Organization ;
    rdfs:label "Acme Platform, Inc." ;
    dcterms:description "SaaS platform providing tenant-isolated data pipelines." .

[] a prov:Entity ;
    rdfs:label "Production Kubernetes cluster (us-west-2)" ;
    dcterms:type "SYSTEM-BOUNDARY" ;
    dcterms:description "In scope: all workloads under namespace prefix tenant-*." .
```

