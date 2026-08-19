# Troubleshooting — v26.8.18

This runbook captures **observed failure modes**, not generic guesses. Start at the failed transition, preserve evidence, repair the narrowest cause, and rerun the boundary that failed before expanding verification.

## First rule

```text
preserve failure -> classify -> locate transition -> form new hypothesis -> repair -> rerun
```

Do not rerun an unchanged failing command repeatedly without a new hypothesis.

## OTel Collector / standing weaver

### Symptom: Collector is healthy but weaver receives no usable spans

Check, in order:

1. Collector receiver accepted-span counters move under a fresh real request.
2. The weaver exporter is configured separately from Jaeger/OCEL.
3. Exporter compression is disabled for weaver (`compression: none`) if the receiver rejects gzip.
4. Kubernetes Service endpoints resolve to the intended Deployment pods.
5. No stale selectorless Service/Endpoints object shadows the Deployment-backed Service.
6. NetworkPolicy permits Collector -> weaver OTLP traffic.
7. weaver is configured not to terminate after an idle interval intended for one-shot use.

Observed historical causes: stale Endpoints shadowing, tonic rejection of default gzip, NetworkPolicy denial, and inactivity timeout.

### Symptom: direct Envoy -> weaver path fails

Do not restore the previously falsified direct path by default. v26.8.18 uses OTel Collector fan-out because direct Envoy-to-weaver OTLP/gRPC and dual-provider Istio approaches failed in live testing.

## Jaeger

### Symptom: OTLP/gRPC arrives as invalid HTTP/1 traffic / bogus greeting

Verify the Jaeger Service port advertises gRPC (`appProtocol: grpc`) and inspect Envoy cluster protocol negotiation. This exact protocol-hint defect was observed and repaired.

## OCEL accumulator

### Symptom: `/ocel-log` reports accumulator unreachable

- verify `ocel-accumulator` Service exists in `istio-system`;
- verify the service port is **4900**;
- verify `OCEL_ACCUMULATOR_URL` if overridden;
- verify NetworkPolicy/service routing;
- query `/status` directly from an admitted in-cluster subject.

A real bug used port 8090 in the proxy while the Service exposed 4900.

### Symptom: status works, discovery fails

At the reviewed v26.8.18 baseline this is an **expected incomplete edge**. `/discovery` must fail closed until the real wasm4pm-cli bridge is implemented and executed. Do not substitute fixture output.

### Symptom: OCEL history disappeared after pod replacement

Current accumulator storage is `emptyDir`. Data loss after pod recreation is consistent with the documented durability ceiling. The fix is persistent storage + recovery verification, not a documentation claim.

## Istio sidecars / NetworkPolicy

### Symptom: injected pods hang during init or cannot contact control plane

Check DNS and istiod egress. A default-deny egress configuration previously blocked sidecars from kube-dns and istiod, causing initialization failure. The lawful repair is a narrow DNS/istiod allow rule, not disabling all NetworkPolicy.

### Symptom: app traffic works without sidecar but fails with STRICT mTLS

Verify both source and destination sidecar injection, PeerAuthentication, Service ports, and NetworkPolicy. Do not weaken STRICT globally before isolating the failed path.

## ggen `/provision`

### Symptom: 503 / binary unavailable

Verify the configured real ggen binary exists and is executable in the service image. Missing binary is intentionally fail-closed; there is no simulated fallback.

### Symptom: tenant namespace resolution crashes around URL quoting

The service previously used `urllib.request.quote`, which does not exist. The corrected path uses `urllib.parse.quote`. If this regresses, static/type checking should catch it even when `py_compile` does not.

### Symptom: receipt verifies now but historical receipts fail after restart

Check signing-key persistence. A locally generated key on ephemeral storage can rotate unintentionally across pod recreation. Recover the historical verifying key if available; do not claim the old receipt chain remains verifiable without it.

### Symptom: `/provision` succeeds but receipt/attempt history disappears

Check the state volume. Ephemeral `emptyDir` is a known current ceiling. Promote to a persistent backing store and execute a restart/recovery test before raising standing.

## ggen marketplace

### Symptom: `/packs` returns fewer/more records than documented

Treat the count as time-bounded observation, not a constant. Re-run the registry bridge against the current admitted packs source. At the reviewed point the observed count was 151.

### Symptom: pack metadata is present but domain ontology queries fail

The generic bridge exposes registry metadata; it does not imply every pack's domain ontology has been imported into one queryable canonical graph. This is a semantic-coverage gap, not necessarily a registry outage.

## Kubernetes admission

### Symptom: Deployment rejected for resources

Inspect the ValidatingAdmissionPolicy result and ensure every container declares both requests and limits in namespaces covered by the policy.

### Symptom: previously running manifest cannot be recreated

Do not assume “was Running” means “is recreatable under current admission.” Compare current PodSecurity/admission policies and checked-in manifest. A real `gymact-status` drift case required backporting `sidecar.istio.io/inject: "false"`/security-context changes for the then-current policy constraints.

## Vulnerability scanning

### Symptom: scan returns zero findings unexpectedly

Verify the real Trivy DB loaded and run a known-vulnerable positive-control image. The v26.8.18 verification deliberately used non-zero findings/positive control to prove the scanner was real.

## Login/session

### Symptom: login returns 200 but browser is immediately unauthenticated on local HTTP

Check cookie `Secure` behavior and `x-forwarded-proto`. A real defect issued Secure cookies on the local HTTP origin; protocol-aware cookie handling repaired it.

## Quota enforcement

### Symptom: workload scales back up and is immediately re-enforced

Check whether the quota-enforcement ConfigMap/threshold remains active. Resetting replicas without clearing or changing the active breach condition can legitimately cause the next controller tick to enforce again.

## Loki / Promtail

If logs are absent, verify:

- Promtail target discovery actually synchronized;
- relabel regex replacement syntax, especially `${1}_` versus `$1_` parsing;
- Loki schema/storage mode compatibility with structured metadata;
- file mounts and actual tailed-file count.

## Evidence-bundle mismatch

If a digest does not verify:

1. preserve the file unchanged;
2. reproduce the documented canonical serialization procedure;
3. distinguish content drift from serializer drift;
4. never overwrite the stored digest merely to make verification pass;
5. regenerate only through the owning evidence process after the cause is understood.

## Escalation

If the failed transition is external authority, missing infrastructure, independent audit, or unavailable provider capability, classify it `BLOCKED` rather than manufacturing a code success. If the mechanism itself does not exist, use `UNSUPPORTED`. If execution was attempted and failed, use `BUILD_BROKEN` or the narrower typed failure/refusal supported by the owning system.
