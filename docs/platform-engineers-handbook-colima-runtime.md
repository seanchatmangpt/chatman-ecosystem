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

## Not done in this pass

- No application/demo workload deployed (Ch05's demo app, or a real chatman-ecosystem
  project) — scoped explicitly to the Ch02 cluster foundation plus Ch04's observability
  stack.
- Keycloak (Ch03), Backstage (Ch06), Crossplane (Ch09) not installed in this pass.

## See also

- [The Platform Engineer's Handbook — ggen Pack](platform-engineers-handbook-ggen-packs.md)
