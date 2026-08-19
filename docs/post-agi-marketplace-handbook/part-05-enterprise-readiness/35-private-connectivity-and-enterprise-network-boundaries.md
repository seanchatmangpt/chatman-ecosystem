# 35. Private Connectivity and Enterprise Network Boundaries

## Network topology can determine whether a sale is admissible

For many Fortune 5 buyers, public internet access is not an acceptable production path even when traffic is strongly encrypted. Private endpoints, private service connectivity, enterprise DNS, proxies, transit networks, customer certificate authorities, egress controls, and disconnected environments can be product requirements.

```text
NetworkAdmission = Topology × Policy × Identity × Verification
```

A marketplace listing cannot compensate for a topology that violates the buyer's security boundary.

## Public TLS versus private path

TLS answers confidentiality/integrity of a transport. Private connectivity answers route and exposure. The product should classify them separately.

A private SaaS projection might require:

```text
customer VPC/VNet/VCN
  ↔ vendor private endpoint/service attachment
  ↔ private DNS
  ↔ seller service
```

The control plane must also be inspected. A data plane reachable privately can still depend on public callbacks, package registries, identity endpoints, telemetry, or support channels that violate customer egress policy.

## Enterprise DNS and addresses

Private integrations fail in practice on mundane topology: overlapping RFC1918 ranges, split-horizon DNS, proxy requirements, MTU, certificate chains, firewall state, or route advertisements. These are part of fulfillment verification.

`READY` requires the customer-visible network postcondition, not simply successful creation of a cloud private-endpoint resource.

## Customer certificate authority

Some deployments require enterprise trust stores or customer-managed certificates. The platform should model certificate issuer, rotation, trust distribution, revocation, and responsibility rather than allowing per-customer shell scripts to become hidden architecture.

## Disconnected environments

An air-gapped/customer-hosted projection must identify every runtime dependency on public registries, entitlement services, package indexes, telemetry, time services, or support endpoints. If commercial entitlement requires continuous public verification, the product is not truly disconnected.

Offline entitlement should be a separate admitted design with expiry, renewal, revocation, audit, and anti-replay semantics.

## Marketplace callbacks

Marketplace commerce itself usually requires external communication. For customer-hosted products, separate the seller's commercial control plane—which can receive marketplace events—from the customer's isolated workload plane. Do not require inbound marketplace callbacks into the customer environment unless the architecture explicitly admits that path.

## Refusals

- `REFUSED:TLS_AS_PRIVATE_NETWORK`
- `REFUSED:PUBLIC_RUNTIME_DEPENDENCY_IN_AIR_GAP`
- `REFUSED:PRIVATE_DATA_PLANE_WITH_UNDECLARED_PUBLIC_CONTROL_PLANE`
- `REFUSED:UNVERIFIED_ROUTE_AS_READY`
- `REFUSED:ONLINE_ONLY_LICENSE_AS_OFFLINE_CAPABILITY`

## Operational exercise

Design three fulfillment classes: normal public SaaS, private-endpoint SaaS, and disconnected customer-hosted Kubernetes. For each, list data/control-plane routes, DNS, certificates, identity, marketplace dependencies, observability, entitlement refresh, support, teardown, and the exact network postconditions required for ALIVE.
