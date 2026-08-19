
# 08 — Subservice organizations & complementary user-entity controls

Every vendor or subprocessor whose controls this system's own SOC 2 scope
depends on — the "carve-out" method (their controls are excluded, only
their existence is disclosed) vs. "inclusive" method (their controls are
tested as part of this engagement) — and any control this project relies
on the *end user* (not the vendor) to operate, a Complementary User-Entity
Control (CUEC).

| Subservice organization | Scope relied upon | Method | CUEC (if any) |
|---|---|---|---|
| Kubernetes control plane images / official container base images (node:20-slim, node:22-slim, python:3.12-slim, python:3.13-slim, rustlang/rust:nightly-slim) | Application and service container images are built FROM these public upstream base images; no evidence of a signed/pinned base-image provenance policy beyond the trivy vulnerability scan described in vuln-scan.ts. | carve-out | Static grep of Dockerfile FROM lines across platform-console. |
| aquasec/trivy (Aqua Security open-source scanner) and its public vulnerability DB mirror (mirror.gcr.io/aquasec/trivy-db) | Used as the platform's real vulnerability-scanning dependency (vuln-scan.ts); the CVE database is pulled from this third-party mirror at scan time, so scan accuracy depends on this external service's data freshness/availability. | carve-out | Read platform-console/app/lib/vuln-scan.ts comments describing the real trivy pull and containerd-socket scan mechanism. |
| GitHub Actions marketplace actions (actions/checkout, dtolnay/rust-toolchain, Swatinem/rust-cache, taiki-e/install-action) | CI admission gate (crown.yml) depends on these pinned third-party GitHub Actions for build/lint/test execution; pinned to specific commit SHAs (not just tags), reducing but not eliminating supply-chain trust in the action publishers. | carve-out | Read .github/workflows/crown.yml. |
| kind (Kubernetes-in-Docker) as the only real cluster substrate | All live k8s verification claims in SONY-READINESS-GAP-CLOSURE.md (RBAC, PodSecurity, admission policy, secret encryption) were run against a single kind cluster on one physical/VM host (kind-platform-eng-colima), not a cloud-managed Kubernetes service -- so none of these controls have been proven against an actual cloud subservice organization (EKS/GKE/AKS) yet. | carve-out | Read SONY-READINESS-GAP-CLOSURE.md verification sections referencing 'kind-platform-eng-colima'. |
| kind / Kubernetes (self-managed, single-node, via colima) | Full control plane, all workloads | carve-out | platform-console/infra/kind-config.yaml pins the node image (kindest/node:v1.34.0) and cluster topology this entire platform runs on. |
| Istio | Service mesh, mTLS enforcement, ingress Gateway/VirtualService routing | carve-out | k8s/mtls.yaml, k8s/mtls-gateway.yaml, k8s/gateway.yaml -- real STRICT PeerAuthentication objects, live-verified traffic enforcement. |
| Supabase (operator + Postgres/GoTrue/PostgREST/Realtime/Storage stack) | Per-project database/auth/REST/storage backend | carve-out | supabase-system namespace operator reconciling Project/SingleDatabase CRDs into per-project Postgres StatefulSets and related Deployments. |
| Prometheus / kube-prometheus-stack (via Helm) and Grafana | Metrics, uptime computation for /status, capacity/cost queries | carve-out | monitoring namespace; ServiceMonitor objects (e.g. k8s/status-page.yaml's platform-prober ServiceMonitor) scraped by this stack; app/lib/status-page.ts and app/lib/cost.ts query it directly. |
| Flux | GitOps reconciliation (installed, no Kustomization/HelmRelease objects active per repo's own disclosure) | carve-out | flux-system namespace, installed but in an admittedly empty GitOps state. |
| Cloud/Kubernetes cluster provider (unspecified, self-hosted per manifests) | Underlying compute, networking, and default-deny NetworkPolicy enforcement that mTLS and RBAC controls depend on. | carve-out | Inferred from k8s manifests (PeerAuthentication, NetworkPolicy, RoleBinding) -- no explicit cloud vendor named in the checked files. |
| Istio service mesh (istio-system namespace, istiod) | Provides the mTLS enforcement (STRICT PeerAuthentication) and the mTLS/MUTUAL Gateway that constitute the primary C1.2 transport-protection control. | carve-out | Direct dependency evident in k8s/mtls.yaml and k8s/mtls-gateway.yaml -- istiod issues/validates certs; the shared istio-ingressgateway Service is explicitly noted as 'not owned by this directory'. |
| Kubernetes cluster (kind, single-node, self-hosted on 'kind-platform-eng-colima') | IaaS control plane: etcd, kube-apiserver, kubelet, RBAC (paas-rbac.yaml), ValidatingAdmissionPolicy admission gates, PodSecurity admission -- all self-managed, not a hyperscaler-managed control plane | carve-out | Confirmed via SONY-READINESS-GAP-CLOSURE.md's real kubectl/etcdctl verification evidence and platform-console/k8s/*.yaml manifests present on disk |
| rustlang/rust:nightly-slim and python:3.12-slim (Docker Hub base images) | Base container images for platform-console/app build (multi-stage Dockerfile) | carve-out | Read platform-console/app/Dockerfile FROM lines directly |
| Docker Hub / OCI registry (implicit, image pull source for the above) | Supplies the base images pulled at build time; no image-signature/provenance verification (cosign, sigstore) found in this repo's Dockerfiles or CI | carve-out | Inferred from FROM directives; absence of a signing-verification step checked by semantic_search with no hits |


## How to declare a subservice organization

```turtle
[] a org:Organization ;
    rdfs:label "AWS (us-west-2)" ;
    dcterms:type "SUBSERVICE-ORG" ;
    dcterms:coverage "Physical security, hypervisor isolation, network infrastructure" ;
    dcterms:accessRights "carve-out" ;
    dcterms:requires "Customer must enable and monitor CloudTrail; AWS provides the logging substrate only." .
```

