/**
 * Real hyperscaler-VPC-console-style Network Topology primitive (AWS VPC
 * console / GCP VPC Network Topology / Azure Virtual Network diagram
 * equivalent) -- Pod/Service CIDR ranges, a per-namespace reachability
 * matrix, and the Istio mTLS trust boundary, all in one place. Every
 * number here comes from a real k8s API read (`lib/k8s.ts`'s
 * `listNodes`/`listAllServices`/`listPods`/`listNetworkPolicies`/
 * `listPeerAuthentications`) or a pure, deterministic computation over
 * that real data -- never a hardcoded CIDR guess or an asserted allow/
 * deny verdict.
 *
 * Split the same way `lib/topology.ts` is: pure functions
 * (`computeObservedCidr`, `buildReachabilityMatrix`) that take already-
 * fetched data and are trivially unit-testable, plus one orchestrator
 * (`getNetworkTopology`) that makes the real k8s calls and wires them
 * together.
 */
import {
  listAllServices,
  listNetworkPolicies,
  listNodes,
  listPeerAuthentications,
  listPodIPs,
  type IamNetworkPolicy,
  type IamPeerAuthentication,
  type K8sNodePodCidr,
} from "./k8s";

// --------------------------------------------------------------- CIDR math
//
// IPv4-only (every real IP on this cluster is IPv4) -- deliberately no
// IPv6 handling rather than a silently-wrong one.

function ipToInt(ip: string): number | null {
  const parts = ip.split(".");
  if (parts.length !== 4) return null;
  let n = 0;
  for (const part of parts) {
    const octet = Number(part);
    if (!Number.isInteger(octet) || octet < 0 || octet > 255) return null;
    n = n * 256 + octet;
  }
  return n >>> 0;
}

function intToIp(n: number): string {
  return [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255].join(".");
}

export interface ObservedCidr {
  /** Smallest CIDR block that contains every observed IP. `null` when
   * zero valid IPv4 addresses were observed. */
  cidr: string | null;
  prefixLength: number | null;
  min: string | null;
  max: string | null;
  /** Count of distinct valid IPv4 addresses this was computed from. */
  sampleCount: number;
}

/**
 * Computes the smallest CIDR block containing every IP in `ips` -- the
 * real, deterministic "smallest common prefix between min and max"
 * algorithm (not a guess, not a fixed /16 or /24 assumption). Pure
 * function, no network calls; unit-testable on its own.
 */
export function computeObservedCidr(ips: string[]): ObservedCidr {
  const values = Array.from(
    new Set(ips.map(ipToInt).filter((n): n is number => n !== null)),
  );
  if (values.length === 0) {
    return { cidr: null, prefixLength: null, min: null, max: null, sampleCount: 0 };
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  // Smallest prefix length such that (min >>> (32-p)) === (max >>> (32-p))
  // for every p from 32 down to 0 -- the standard "common-prefix CIDR
  // block containing both endpoints" computation.
  let prefixLength = 32;
  for (let p = 32; p >= 0; p--) {
    const shift = 32 - p;
    const maskedMin = shift >= 32 ? 0 : (min >>> shift) << shift;
    const maskedMax = shift >= 32 ? 0 : (max >>> shift) << shift;
    if (maskedMin === maskedMax) {
      prefixLength = p;
      break;
    }
  }
  const shift = 32 - prefixLength;
  const network = shift >= 32 ? 0 : (min >>> shift) << shift;
  return {
    cidr: `${intToIp(network >>> 0)}/${prefixLength}`,
    prefixLength,
    min: intToIp(min),
    max: intToIp(max),
    sampleCount: values.length,
  };
}

export interface ClusterCidrInfo {
  podCidr: {
    /** Real, authoritative per-node allocations from `Node.spec.podCIDR`
     * -- kubeadm's own node-ipam controller writes this. */
    authoritative: K8sNodePodCidr[];
    /** Real observed range computed from live Pod IPs across the
     * platform namespaces this console has `pods` RBAC for -- provided
     * as corroboration of the authoritative value above, not a
     * replacement for it. */
    observed: ObservedCidr;
    method: "authoritative (Node.spec.podCIDR), corroborated by observed live Pod IPs";
  };
  serviceCidr: {
    /** No RBAC exists into kube-system, so there is no config-flag
     * source for this -- the ONLY value here is the smallest CIDR block
     * containing every real, live Service ClusterIP across every
     * namespace. */
    observed: ObservedCidr;
    method: "observed only (derived from live Service ClusterIPs) -- kube-apiserver's --service-cluster-ip-range flag and the kubeadm-config ConfigMap both live in kube-system, which this console deliberately has no RBAC into";
  };
}

/**
 * Real Pod/Service CIDR info. `podNamespaces` should be the platform
 * namespaces this console already holds per-namespace `pods` RBAC for
 * (the same list `/logs` and `/registry` use) -- passed in rather than
 * hardcoded here so this module has no namespace list of its own to
 * drift out of sync with theirs.
 */
export async function getClusterCidrInfo(
  podNamespaces: string[],
): Promise<{ ok: true; data: ClusterCidrInfo } | { ok: false; error: string }> {
  const [nodesResult, servicesResult, podIpResults] = await Promise.all([
    listNodes(),
    listAllServices(),
    Promise.all(podNamespaces.map((ns) => listPodIPs(ns))),
  ]);

  if (!nodesResult.ok) return nodesResult;
  if (!servicesResult.ok) return servicesResult;

  // Fail-closed per-namespace, same convention `buildTopologySnapshot`
  // uses: a namespace this console can't read pods in (RBAC boundary or
  // transient error) contributes zero samples to the observed range,
  // never a fabricated "0 pods here".
  const observedPodIps = podIpResults.flatMap((r) => (r.ok ? r.data : []));
  const podObserved = computeObservedCidr(observedPodIps);

  const serviceIps = servicesResult.data
    .map((s) => s.clusterIP)
    .filter((ip): ip is string => !!ip && ip !== "None");
  const serviceObserved = computeObservedCidr(serviceIps);

  return {
    ok: true,
    data: {
      podCidr: {
        authoritative: nodesResult.data,
        observed: podObserved,
        method: "authoritative (Node.spec.podCIDR), corroborated by observed live Pod IPs",
      },
      serviceCidr: {
        observed: serviceObserved,
        method:
          "observed only (derived from live Service ClusterIPs) -- kube-apiserver's --service-cluster-ip-range flag and the kubeadm-config ConfigMap both live in kube-system, which this console deliberately has no RBAC into",
      },
    },
  };
}

// --------------------------------------------------------- Reachability

export type ReachabilityVerdict = "allow" | "deny";

export interface ReachabilityCell {
  source: string;
  target: string;
  verdict: ReachabilityVerdict;
  /** Real policy name(s) this verdict was computed from -- empty when
   * the target namespace has zero Ingress-type NetworkPolicy at all
   * (k8s' own default-allow-when-unselected behavior). */
  policyNames: string[];
  reason: string;
}

export interface ReachabilityMatrix {
  namespaces: string[];
  cells: ReachabilityCell[];
}

/**
 * Builds a real per-namespace-pair Ingress reachability matrix from
 * ACTUALLY-APPLIED NetworkPolicy objects only -- reuses the exact
 * `ingressFromNamespaces` field `lib/k8s.ts`'s `listNetworkPolicies`
 * already computes from each policy's real
 * `spec.ingress[].from[].namespaceSelector.matchLabels
 * ['kubernetes.io/metadata.name']`, the same field `/topology`'s arcs
 * already draw from. Pure function, no network calls.
 *
 * Real k8s semantics implemented here, not simplified away:
 *  - A namespace with ZERO NetworkPolicy carrying `Ingress` in
 *    `policyTypes` has NO ingress restriction at all (k8s' documented
 *    default-allow-when-unselected behavior) -- every source is `allow`.
 *  - A namespace with at least one such policy is default-deny for
 *    ingress; a source is `allow` only if the UNION of every Ingress
 *    policy's `ingressFromNamespaces` (multiple policies are OR'd
 *    together in real NetworkPolicy semantics) names that source. A
 *    policy with an Ingress policyType but zero `ingress` rules (a
 *    `*-default-deny`-shaped object) contributes nothing to that union,
 *    exactly like real enforcement.
 *  - Self-pairs (`source === target`) are computed by this exact same
 *    rule, not hardcoded to `allow` -- a namespace whose only Ingress
 *    rule names a different namespace (this cluster's real
 *    `*-allow-from-platform-console` shape) genuinely denies same-
 *    namespace pod-to-pod ingress too, and this matrix reports that
 *    honestly rather than assuming same-namespace traffic is always
 *    permitted.
 */
export function buildReachabilityMatrix(
  namespaces: string[],
  policies: IamNetworkPolicy[],
): ReachabilityMatrix {
  const cells: ReachabilityCell[] = [];

  for (const target of namespaces) {
    const targetPolicies = policies.filter((p) => p.namespace === target);
    const ingressPolicies = targetPolicies.filter((p) => p.policyTypes.includes("Ingress"));

    if (ingressPolicies.length === 0) {
      for (const source of namespaces) {
        cells.push({
          source,
          target,
          verdict: "allow",
          policyNames: [],
          reason: `no NetworkPolicy in ${target} carries policyType Ingress -- k8s' default-allow-when-unselected applies`,
        });
      }
      continue;
    }

    // Union of allowed source namespaces, tracking which real policy
    // object(s) named each one.
    const allowedBy = new Map<string, string[]>();
    for (const policy of ingressPolicies) {
      for (const ns of policy.ingressFromNamespaces) {
        const list = allowedBy.get(ns) ?? [];
        list.push(policy.name);
        allowedBy.set(ns, list);
      }
    }
    const denyPolicyNames = ingressPolicies
      .filter((p) => p.ingressFromNamespaces.length === 0)
      .map((p) => p.name);

    for (const source of namespaces) {
      const allowingPolicies = allowedBy.get(source);
      if (allowingPolicies) {
        cells.push({
          source,
          target,
          verdict: "allow",
          policyNames: allowingPolicies,
          reason: `${allowingPolicies.join(", ")} in ${target} names ${source} via namespaceSelector`,
        });
      } else {
        cells.push({
          source,
          target,
          verdict: "deny",
          policyNames: ingressPolicies.map((p) => p.name),
          reason:
            denyPolicyNames.length > 0
              ? `${target} is default-deny for Ingress (${denyPolicyNames.join(", ")}) and no policy names ${source} as an allowed source`
              : `${target}'s Ingress policies (${ingressPolicies.map((p) => p.name).join(", ")}) do not name ${source} as an allowed source`,
        });
      }
    }
  }

  return { namespaces, cells };
}

// ------------------------------------------------------------- mTLS boundary

export interface NamespaceMtlsStatus {
  namespace: string;
  /** The namespace-wide PeerAuthentication (no `spec.selector`), if any. */
  namespaceWide: IamPeerAuthentication | null;
  /** Any additional workload-scoped (`spec.selector` present) overrides
   * in this namespace -- surfaced, never hidden, since they mean not
   * every pod in the namespace follows `namespaceWide`'s mode. */
  workloadOverrides: IamPeerAuthentication[];
}

/**
 * Groups real PeerAuthentication objects by namespace for every
 * namespace passed in. Namespaces with zero PeerAuthentication objects
 * get `namespaceWide: null` -- an honest "no explicit policy found on
 * this cluster" rather than an assumed mode, since confirming Istio's
 * documented PERMISSIVE mesh-wide fallback would require reading the
 * `istio` ConfigMap in istio-system, which this console has no RBAC
 * for (deliberately -- see k8s/paas-rbac.yaml).
 */
export function buildMtlsBoundary(
  namespaces: string[],
  peerAuths: IamPeerAuthentication[],
): NamespaceMtlsStatus[] {
  return namespaces.map((namespace) => {
    const inNs = peerAuths.filter((p) => p.namespace === namespace);
    return {
      namespace,
      namespaceWide: inNs.find((p) => !p.workloadScoped) ?? null,
      workloadOverrides: inNs.filter((p) => p.workloadScoped),
    };
  });
}

// ------------------------------------------------------------ Orchestrator

export interface NetworkTopologySnapshot {
  cidr: ClusterCidrInfo;
  reachability: ReachabilityMatrix;
  mtls: NamespaceMtlsStatus[];
  policyError: string | null;
  peerAuthError: string | null;
  cidrError: string | null;
}

/**
 * Makes the real k8s calls (Nodes, cluster-wide Services, per-namespace
 * Pods for the CIDR corroboration, cluster-wide NetworkPolicies,
 * cluster-wide PeerAuthentications) and wires them through the pure
 * functions above. `namespaces` is the platform namespace list the page
 * passes in (same convention as `buildTopologySnapshot`).
 */
export async function getNetworkTopology(namespaces: string[]): Promise<NetworkTopologySnapshot> {
  const [cidrResult, policiesResult, peerAuthResult] = await Promise.all([
    getClusterCidrInfo(namespaces),
    listNetworkPolicies(),
    listPeerAuthentications(),
  ]);

  const emptyCidr: ClusterCidrInfo = {
    podCidr: {
      authoritative: [],
      observed: { cidr: null, prefixLength: null, min: null, max: null, sampleCount: 0 },
      method: "authoritative (Node.spec.podCIDR), corroborated by observed live Pod IPs",
    },
    serviceCidr: {
      observed: { cidr: null, prefixLength: null, min: null, max: null, sampleCount: 0 },
      method:
        "observed only (derived from live Service ClusterIPs) -- kube-apiserver's --service-cluster-ip-range flag and the kubeadm-config ConfigMap both live in kube-system, which this console deliberately has no RBAC into",
    },
  };

  const policies = policiesResult.ok ? policiesResult.data : [];
  const peerAuths = peerAuthResult.ok ? peerAuthResult.data : [];

  return {
    cidr: cidrResult.ok ? cidrResult.data : emptyCidr,
    reachability: buildReachabilityMatrix(namespaces, policies),
    mtls: buildMtlsBoundary(namespaces, peerAuths),
    policyError: policiesResult.ok ? null : policiesResult.error,
    peerAuthError: peerAuthResult.ok ? null : peerAuthResult.error,
    cidrError: cidrResult.ok ? null : cidrResult.error,
  };
}
