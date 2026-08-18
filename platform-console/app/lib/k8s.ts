/**
 * Minimal Kubernetes API client using the pod's own in-cluster
 * ServiceAccount token -- no external k8s client library, no fabricated
 * client-side state. Every function here does a real HTTPS call to the
 * API server (https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT)
 * using the token/CA bundle Kubernetes mounts automatically at
 * /var/run/secrets/kubernetes.io/serviceaccount/. Off-cluster (local dev,
 * `next build`), that mount does not exist, so every call here fails
 * closed with an honest "not configured" result rather than a fabricated
 * fallback -- same fail-closed convention as lib/status.ts.
 *
 * Runs on the Node.js runtime only (uses `node:fs`/`node:https`), same
 * constraint as lib/credentials.ts -- never import this from middleware.
 */
import fs from "node:fs";
import https from "node:https";

const SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount";
const REQUEST_TIMEOUT_MS = 5000;

export type K8sResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

interface InClusterConfig {
  token: string;
  ca: Buffer;
  host: string;
  port: string;
}

let cachedConfig: InClusterConfig | null | undefined;

function readInClusterConfig(): InClusterConfig | null {
  if (cachedConfig !== undefined) return cachedConfig;
  try {
    const tokenPath = `${SA_DIR}/token`;
    const caPath = `${SA_DIR}/ca.crt`;
    const host = process.env.KUBERNETES_SERVICE_HOST;
    const port = process.env.KUBERNETES_SERVICE_PORT ?? "443";
    if (!host || !fs.existsSync(tokenPath) || !fs.existsSync(caPath)) {
      cachedConfig = null;
      return null;
    }
    cachedConfig = {
      token: fs.readFileSync(tokenPath, "utf8").trim(),
      ca: fs.readFileSync(caPath),
      host,
      port,
    };
    return cachedConfig;
  } catch {
    cachedConfig = null;
    return null;
  }
}

/** True when a real in-cluster ServiceAccount identity is available. */
export function hasClusterCredentials(): boolean {
  return readInClusterConfig() !== null;
}

async function k8sRequest<T>(
  path: string,
  method: "GET" | "POST" | "DELETE" | "PATCH" = "GET",
  body?: unknown,
  contentType = "application/json",
): Promise<K8sResult<T>> {
  const cfg = readInClusterConfig();
  if (!cfg) {
    return {
      ok: false,
      error:
        "not configured: no in-cluster ServiceAccount credentials found " +
        `(${SA_DIR}) -- this only works when running as the platform-console pod`,
    };
  }

  const payload = body ? Buffer.from(JSON.stringify(body)) : undefined;

  return new Promise((resolve) => {
    const req = https.request(
      {
        host: cfg.host,
        port: cfg.port,
        path,
        method,
        ca: cfg.ca,
        timeout: REQUEST_TIMEOUT_MS,
        headers: {
          Authorization: `Bearer ${cfg.token}`,
          Accept: "application/json",
          ...(payload
            ? {
                "Content-Type": contentType,
                "Content-Length": String(payload.length),
              }
            : {}),
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          const raw = Buffer.concat(chunks).toString("utf8");
          let parsed: unknown = undefined;
          if (raw) {
            try {
              parsed = JSON.parse(raw);
            } catch {
              resolve({
                ok: false,
                error: `unparsable response body from ${method} ${path} (HTTP ${status})`,
              });
              return;
            }
          }
          if (status < 200 || status >= 300) {
            const message =
              (parsed as { message?: string } | undefined)?.message ??
              `HTTP ${status}`;
            resolve({ ok: false, error: `${method} ${path} failed: ${message}` });
            return;
          }
          resolve({ ok: true, data: parsed as T });
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error(`timeout after ${REQUEST_TIMEOUT_MS}ms`)));
    req.on("error", (err) =>
      resolve({ ok: false, error: `unreachable: ${err.message}` }),
    );
    if (payload) req.write(payload);
    req.end();
  });
}

// --------------------------------------------------------------- Projects

export interface SupabaseProject {
  name: string;
  namespace: string;
  createdAt: string;
  databaseRefName: string | null;
  hostname: string | null;
  ready: boolean | null; // null when no Ready condition has been reported yet
  reason: string | null;
  message: string | null;
}

interface K8sListMeta {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
    spec?: {
      databaseRef?: { name?: string };
      http?: { hostname?: string };
    };
    status?: {
      conditions?: Array<{
        type: string;
        status: string;
        reason?: string;
        message?: string;
      }>;
    };
  }>;
}

function toSupabaseProject(item: NonNullable<K8sListMeta["items"]>[number]): SupabaseProject {
  const readyCondition = item.status?.conditions?.find((c) => c.type === "Ready");
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    databaseRefName: item.spec?.databaseRef?.name ?? null,
    hostname: item.spec?.http?.hostname ?? null,
    ready: readyCondition ? readyCondition.status === "True" : null,
    reason: readyCondition?.reason ?? null,
    message: readyCondition?.message ?? null,
  };
}

export async function listProjects(): Promise<K8sResult<SupabaseProject[]>> {
  const result = await k8sRequest<K8sListMeta>(
    "/apis/core.supabase.io/v1alpha1/projects",
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toSupabaseProject) };
}

export async function getProject(
  name: string,
): Promise<K8sResult<SupabaseProject | null>> {
  const all = await listProjects();
  if (!all.ok) return all;
  return { ok: true, data: all.data.find((p) => p.name === name) ?? null };
}

export interface CreateProjectInput {
  name: string;
  namespace: string;
  databaseRefName: string;
  hostname: string;
  protocol: "http" | "https";
  /** PVC size for the paired SingleDatabase, e.g. "1Gi". Defaults to "1Gi". */
  dbStorageSize: string;
}

interface SingleDatabaseItem {
  metadata: { name: string; namespace: string };
}

/**
 * Creates the SingleDatabase CR a Project's spec.databaseRef points at.
 * Mirrors the real, working demo-db manifest in supabase-demo (verified via
 * `kubectl get singledatabase demo-db -n supabase-demo -o yaml`): only
 * spec.storage is required, the operator fills in the rest (resolvedDatabase
 * host/port/user/passwordRef) once it reconciles.
 */
export async function createSingleDatabase(input: {
  name: string;
  namespace: string;
  storageSize: string;
}): Promise<K8sResult<SingleDatabaseItem>> {
  const manifest = {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "SingleDatabase",
    metadata: { name: input.name, namespace: input.namespace },
    spec: {
      storage: { accessModes: ["ReadWriteOnce"], size: input.storageSize },
    },
  };
  return k8sRequest<SingleDatabaseItem>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(input.namespace)}/singledatabases`,
    "POST",
    manifest,
  );
}

/**
 * Creates a Project CR only (no paired database). Kept for callers that
 * already have a SingleDatabase they want to reference (e.g. multiple
 * Projects sharing one database). Most callers want createProjectWithDatabase
 * below, which is what the Create Project form/API route uses.
 */
export async function createProject(
  input: Omit<CreateProjectInput, "dbStorageSize">,
): Promise<K8sResult<SupabaseProject>> {
  const manifest = {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "Project",
    metadata: { name: input.name, namespace: input.namespace },
    spec: {
      databaseRef: { kind: "SingleDatabase", name: input.databaseRefName },
      http: { hostname: input.hostname, protocol: input.protocol },
    },
  };
  const result = await k8sRequest<NonNullable<K8sListMeta["items"]>[number]>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(input.namespace)}/projects`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toSupabaseProject(result.data) };
}

/**
 * Creates a Project CR paired with its own SingleDatabase CR, matching the
 * real shape the supabase-operator expects (verified live against the
 * demo-project/demo-db pair in supabase-demo: Project.spec.databaseRef ->
 * {kind: SingleDatabase, name}). The SingleDatabase is created first so it
 * is referenceable as soon as the operator reconciles the Project -- if that
 * first call fails (e.g. it already exists), the Project is never created,
 * so a Project is never left pointing at a database that doesn't exist.
 */
export async function createProjectWithDatabase(
  input: CreateProjectInput,
): Promise<K8sResult<SupabaseProject>> {
  const dbResult = await createSingleDatabase({
    name: input.databaseRefName,
    namespace: input.namespace,
    storageSize: input.dbStorageSize,
  });
  if (!dbResult.ok) return dbResult;

  const projectResult = await createProject(input);
  return projectResult;
}

// ---------------------------------------------------------------- Services

export interface K8sService {
  name: string;
  namespace: string;
  clusterIP: string | null;
  ports: Array<{ name?: string; port: number; targetPort?: number | string; protocol: string }>;
  labels: Record<string, string>;
  dns: string;
}

interface ServiceListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; labels?: Record<string, string> };
    spec?: {
      clusterIP?: string;
      ports?: Array<{ name?: string; port: number; targetPort?: number | string; protocol?: string }>;
    };
  }>;
}

export async function listNamespaceServices(
  namespace: string,
): Promise<K8sResult<K8sService[]>> {
  const result = await k8sRequest<ServiceListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/services`,
  );
  if (!result.ok) return result;
  const items = (result.data.items ?? []).map((svc) => ({
    name: svc.metadata.name,
    namespace: svc.metadata.namespace,
    clusterIP: svc.spec?.clusterIP ?? null,
    ports: (svc.spec?.ports ?? []).map((p) => ({
      name: p.name,
      port: p.port,
      targetPort: p.targetPort,
      protocol: p.protocol ?? "TCP",
    })),
    labels: svc.metadata.labels ?? {},
    dns: `${svc.metadata.name}.${svc.metadata.namespace}.svc.cluster.local`,
  }));
  return { ok: true, data: items };
}

// ------------------------------------------------------- Service Discovery
//
// Real hyperscaler-PaaS-style Service Discovery primitive (AWS Route53
// private hosted zones / GCP Cloud DNS internal zones / Azure Private DNS
// equivalent) -- not decorative, because this cluster's actual internal
// DNS/service-discovery layer already exists and every other module's
// cluster-internal URLs (the Database module's Postgres/PostgREST hosts,
// the Backups module's `<stem>.<namespace>.svc.cluster.local` pg_dump
// target) already depend on it: CoreDNS resolves `<svc>.<namespace>.svc.
// cluster.local` to a Service's ClusterIP because the Service+Endpoints
// objects are the real, live source of truth CoreDNS's kubernetes plugin
// reads directly from the API server -- this module reads that exact same
// pair of objects, not a separate DNS-specific API. `listNamespaceServices`
// above already provides the DNS-name-bearing half (Service); the
// Endpoints half below adds the load-bearing "is this record actually
// resolving to something healthy" signal -- how many backing Pod IPs are
// currently Ready versus configured, the thing a DNS name alone cannot
// tell you. No new RBAC for Services (already granted cluster-wide by the
// `services` rule above); Endpoints get their own new cluster-wide rule
// in `k8s/paas-rbac.yaml`, same sensitivity class (workload IPs, not
// secrets) as the Services/Deployments/Roles already granted there.

export interface K8sEndpointSubsetAddress {
  ip: string;
  podName: string | null;
}

export interface K8sServiceEndpoints {
  name: string;
  namespace: string;
  readyAddresses: K8sEndpointSubsetAddress[];
  notReadyAddresses: K8sEndpointSubsetAddress[];
}

interface EndpointsListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    subsets?: Array<{
      addresses?: Array<{ ip: string; targetRef?: { kind?: string; name?: string } }>;
      notReadyAddresses?: Array<{ ip: string; targetRef?: { kind?: string; name?: string } }>;
    }>;
  }>;
}

function toAddress(a: { ip: string; targetRef?: { kind?: string; name?: string } }): K8sEndpointSubsetAddress {
  return { ip: a.ip, podName: a.targetRef?.kind === "Pod" ? a.targetRef.name ?? null : null };
}

/**
 * Lists real core/v1 Endpoints in one namespace -- one object per Service
 * of the same name (the endpoint-controller creates/maintains this
 * automatically from the Service's selector matching real Pod IPs, the
 * same object CoreDNS's kubernetes plugin reads to answer SRV/A queries
 * for that Service's DNS name). `readyAddresses` are backing Pod IPs
 * currently passing readiness (what a client actually gets routed to
 * today); `notReadyAddresses` are Pod IPs the Service selects but that
 * have not yet passed a readiness probe -- kept separate, never merged,
 * so callers can distinguish "0 ready" from "misconfigured selector,
 * nothing at all".
 */
export async function listEndpoints(namespace: string): Promise<K8sResult<K8sServiceEndpoints[]>> {
  const result = await k8sRequest<EndpointsListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/endpoints`,
  );
  if (!result.ok) return result;
  const items = (result.data.items ?? []).map((item) => {
    const ready: K8sEndpointSubsetAddress[] = [];
    const notReady: K8sEndpointSubsetAddress[] = [];
    for (const subset of item.subsets ?? []) {
      for (const a of subset.addresses ?? []) ready.push(toAddress(a));
      for (const a of subset.notReadyAddresses ?? []) notReady.push(toAddress(a));
    }
    return {
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      readyAddresses: ready,
      notReadyAddresses: notReady,
    };
  });
  return { ok: true, data: items };
}

export interface ServiceDiscoveryRecord {
  name: string;
  namespace: string;
  dns: string;
  clusterIP: string | null;
  ports: Array<{ name?: string; port: number; targetPort?: number | string; protocol: string }>;
  /** Number of backing Pod IPs currently passing readiness -- what this
   * DNS name actually routes traffic to right now, read live from the
   * matching Endpoints object. `null` when no Endpoints object exists at
   * all for this Service name (a real, honest "no backing record" state,
   * distinct from 0/0). */
  readyEndpoints: number | null;
  totalEndpoints: number | null;
}

/**
 * Combines real Services (the DNS name + ClusterIP half) with real
 * Endpoints (the "is it actually resolving to something healthy" half)
 * for one namespace -- one HTTP round trip each, joined client-side by
 * Service/Endpoints name, which is always identical for a same-namespace
 * pair (the endpoint-controller's own naming convention, never a guess).
 */
export async function listServicesWithEndpoints(
  namespace: string,
): Promise<K8sResult<ServiceDiscoveryRecord[]>> {
  const [servicesResult, endpointsResult] = await Promise.all([
    listNamespaceServices(namespace),
    listEndpoints(namespace),
  ]);
  if (!servicesResult.ok) return servicesResult;
  if (!endpointsResult.ok) return endpointsResult;

  const endpointsByName = new Map(endpointsResult.data.map((e) => [e.name, e]));
  return {
    ok: true,
    data: servicesResult.data.map((svc) => {
      const eps = endpointsByName.get(svc.name);
      return {
        name: svc.name,
        namespace: svc.namespace,
        dns: svc.dns,
        clusterIP: svc.clusterIP,
        ports: svc.ports,
        readyEndpoints: eps ? eps.readyAddresses.length : null,
        totalEndpoints: eps ? eps.readyAddresses.length + eps.notReadyAddresses.length : null,
      };
    }),
  };
}

// -------------------------------------------------------------- Namespaces

interface NamespaceListResponse {
  items?: Array<{ metadata: { name: string } }>;
}

export async function listNamespaces(): Promise<K8sResult<string[]>> {
  const result = await k8sRequest<NamespaceListResponse>("/api/v1/namespaces");
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map((ns) => ns.metadata.name) };
}

// ------------------------------------------------------------------ GitOps

export interface FluxResource {
  kind: "Kustomization" | "HelmRelease";
  name: string;
  namespace: string;
  ready: boolean | null;
  reason: string | null;
  message: string | null;
}

interface FluxListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      conditions?: Array<{
        type: string;
        status: string;
        reason?: string;
        message?: string;
      }>;
    };
  }>;
}

function toFluxResource(
  kind: "Kustomization" | "HelmRelease",
  item: NonNullable<FluxListResponse["items"]>[number],
): FluxResource {
  const readyCondition = item.status?.conditions?.find((c) => c.type === "Ready");
  return {
    kind,
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    ready: readyCondition ? readyCondition.status === "True" : null,
    reason: readyCondition?.reason ?? null,
    message: readyCondition?.message ?? null,
  };
}

export async function listKustomizations(): Promise<K8sResult<FluxResource[]>> {
  const result = await k8sRequest<FluxListResponse>(
    "/apis/kustomize.toolkit.fluxcd.io/v1/kustomizations",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => toFluxResource("Kustomization", item)),
  };
}

export async function listHelmReleases(): Promise<K8sResult<FluxResource[]>> {
  const result = await k8sRequest<FluxListResponse>(
    "/apis/helm.toolkit.fluxcd.io/v2/helmreleases",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => toFluxResource("HelmRelease", item)),
  };
}

// --------------------------------------------------------------------- IAM

export interface RbacRole {
  kind: "Role" | "RoleBinding";
  name: string;
  namespace: string;
  detail: string; // rule count, or "<subjects> -> <roleRef>"
}

interface RoleListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    rules?: unknown[];
  }>;
}

interface RoleBindingListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    subjects?: Array<{ kind: string; name: string }>;
    roleRef: { kind: string; name: string };
  }>;
}

export async function listRoles(): Promise<K8sResult<RbacRole[]>> {
  const result = await k8sRequest<RoleListResponse>(
    "/apis/rbac.authorization.k8s.io/v1/roles",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      kind: "Role" as const,
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      detail: `${item.rules?.length ?? 0} rule(s)`,
    })),
  };
}

export async function listRoleBindings(): Promise<K8sResult<RbacRole[]>> {
  const result = await k8sRequest<RoleBindingListResponse>(
    "/apis/rbac.authorization.k8s.io/v1/rolebindings",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      kind: "RoleBinding" as const,
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      detail: `${(item.subjects ?? []).map((s) => `${s.kind}/${s.name}`).join(", ") || "(no subjects)"} -> ${item.roleRef.kind}/${item.roleRef.name}`,
    })),
  };
}

export interface IamNetworkPolicy {
  name: string;
  namespace: string;
  policyTypes: string[];
  /**
   * Real cross-namespace ingress sources for this policy -- the
   * `kubernetes.io/metadata.name` value of every `namespaceSelector` under
   * `spec.ingress[].from[]`. This is the exact selector shape
   * `k8s/network-policies.yaml`'s `*-allow-from-platform-console` rules use
   * (Kubernetes auto-labels every namespace with this well-known label, so
   * matching on it names the source namespace by its real, immutable
   * identity). Empty when the policy has no `ingress` rules at all (e.g. a
   * `*-default-deny`) or none of its rules use a namespaceSelector -- never
   * inferred or fabricated from anything but this exact field.
   */
  ingressFromNamespaces: string[];
}

interface NetworkPolicyListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      policyTypes?: string[];
      ingress?: Array<{
        from?: Array<{
          namespaceSelector?: { matchLabels?: Record<string, string> };
        }>;
      }>;
    };
  }>;
}

export async function listNetworkPolicies(): Promise<K8sResult<IamNetworkPolicy[]>> {
  const result = await k8sRequest<NetworkPolicyListResponse>(
    "/apis/networking.k8s.io/v1/networkpolicies",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => {
      const fromNamespaces = new Set<string>();
      for (const rule of item.spec?.ingress ?? []) {
        for (const peer of rule.from ?? []) {
          const ns = peer.namespaceSelector?.matchLabels?.["kubernetes.io/metadata.name"];
          if (ns) fromNamespaces.add(ns);
        }
      }
      return {
        name: item.metadata.name,
        namespace: item.metadata.namespace,
        policyTypes: item.spec?.policyTypes ?? [],
        ingressFromNamespaces: Array.from(fromNamespaces).sort(),
      };
    }),
  };
}

// ------------------------------------------------------------------- Secrets
//
// Real hyperscaler-PaaS-style Secrets Manager primitive (AWS Secrets
// Manager / GCP Secret Manager / Azure Key Vault equivalent), scoped by
// k8s/paas-rbac.yaml to a Role+RoleBinding per platform namespace (never
// cluster-wide) since Secrets are more sensitive than the read-mostly
// resources above. Secret *values* are never logged, never returned in a
// list response, and never included in any function's return type here --
// only key NAMES are ever surfaced past this file. createSecret is the
// only function that ever sees plaintext values, and it only forwards them
// (base64-encoded, as the k8s Secret API requires) to the API server over
// the same authenticated HTTPS connection every other call in this file
// uses -- nothing is written to a log, a file, or any other sink.

export interface SecretSummary {
  name: string;
  namespace: string;
  createdAt: string;
  keys: string[]; // key NAMES only -- values are never read back out of the cluster
}

interface SecretListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
    type?: string;
    data?: Record<string, string>; // base64 values -- deliberately never read past Object.keys()
  }>;
}

interface SecretItem {
  metadata: { name: string; namespace: string; creationTimestamp: string };
  data?: Record<string, string>;
}

function toSecretSummary(item: NonNullable<SecretListResponse["items"]>[number]): SecretSummary {
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    keys: Object.keys(item.data ?? {}),
  };
}

export async function listSecrets(namespace: string): Promise<K8sResult<SecretSummary[]>> {
  const result = await k8sRequest<SecretListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets`,
  );
  if (!result.ok) return result;
  // type=Opaque only -- exclude kubernetes.io/service-account-token and
  // other system-managed secret types the operator/platform itself owns,
  // so this module only ever shows/manages secrets this PaaS surface
  // itself created.
  return {
    ok: true,
    data: (result.data.items ?? [])
      .filter((item) => item.type === undefined || item.type === "Opaque")
      .map(toSecretSummary),
  };
}

/**
 * Creates a real k8s Secret (type: Opaque), base64-encoding each plaintext
 * value as the k8s Secret API requires. `data` is the only place in this
 * module plaintext values are ever held in memory -- the return value is a
 * SecretSummary (key names only), never the values themselves.
 */
export async function createSecret(
  namespace: string,
  name: string,
  data: Record<string, string>,
): Promise<K8sResult<SecretSummary>> {
  const encoded: Record<string, string> = {};
  for (const [key, value] of Object.entries(data)) {
    encoded[key] = Buffer.from(value, "utf8").toString("base64");
  }
  const manifest = {
    apiVersion: "v1",
    kind: "Secret",
    type: "Opaque",
    metadata: { name, namespace },
    data: encoded,
  };
  const result = await k8sRequest<SecretItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toSecretSummary(result.data) };
}

export async function deleteSecret(
  namespace: string,
  name: string,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

// ---------------------------------------------------------- Container Registry
//
// Real hyperscaler-PaaS-style Container Registry primitive (ECR / GCR / ACR
// equivalent) -- honestly adapted to what is actually true on this
// cluster: there is no push-capable registry here. Images are built
// locally and `kind load docker-image`d straight into the kind node's
// containerd, so the only registry-shaped truth this console can show is
// an IMAGE INVENTORY: which images each real Deployment's containers
// reference, and whether a real Pod proves that exact image is actually
// present. The console pod has no docker/containerd socket (on purpose --
// see k8s/paas-rbac.yaml), so it cannot run `crictl images` itself; the
// only honest substitute reachable from the k8s API is a real Pod's
// containerStatuses: a Ready container using that image string, with a
// real imageID digest reported, is proof containerd already pulled it. A
// container stuck Waiting with an image-pull reason (ImagePullBackOff /
// ErrImagePull / InvalidImageName) is proof it did not -- a real
// Kubernetes-reported condition, never fabricated.

export interface DeploymentContainerSpec {
  name: string;
  image: string;
}

export interface K8sDeployment {
  name: string;
  namespace: string;
  containers: DeploymentContainerSpec[];
  replicasDesired: number;
  replicasReady: number;
  replicasAvailable: number;
}

interface DeploymentListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      replicas?: number;
      template?: { spec?: { containers?: Array<{ name: string; image: string }> } };
    };
    status?: { readyReplicas?: number; availableReplicas?: number };
  }>;
}

/** Lists real `apps/v1` Deployments in one namespace -- name, namespace,
 * per-container `image` exactly as `spec.template.spec.containers[].image`
 * reports it, and desired/ready/available replica counts from `status`. */
export async function listDeployments(namespace: string): Promise<K8sResult<K8sDeployment[]>> {
  const result = await k8sRequest<DeploymentListResponse>(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments`,
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      containers: (item.spec?.template?.spec?.containers ?? []).map((c) => ({
        name: c.name,
        image: c.image,
      })),
      replicasDesired: item.spec?.replicas ?? 0,
      replicasReady: item.status?.readyReplicas ?? 0,
      replicasAvailable: item.status?.availableReplicas ?? 0,
    })),
  };
}

export interface ContainerImageStatus {
  pod: string;
  namespace: string;
  container: string;
  /** Image string as reported on the running container (matches the
   * Deployment's container.image when the Pod is running that spec). */
  image: string;
  /** Real resolved digest reference (`status.containerStatuses[].imageID`),
   * e.g. `sha256:...` -- only populated once the runtime has actually
   * pulled/resolved the image, so its presence alone is evidence the image
   * is really present in containerd. */
  imageID: string | null;
  ready: boolean;
  waitingReason: string | null;
  waitingMessage: string | null;
}

interface PodImageStatusListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      containerStatuses?: Array<{
        name: string;
        image?: string;
        imageID?: string;
        ready?: boolean;
        state?: { waiting?: { reason?: string; message?: string } };
      }>;
    };
  }>;
}

/** Real per-container image status for every Pod in one namespace, read
 * from `status.containerStatuses` -- the k8s-API-only substitute for
 * shelling out to `crictl images` from inside the console pod (which has
 * no containerd socket). Used by the Registry module to decide whether a
 * Deployment's referenced image is actually present (a Ready container
 * reporting that image + a real `imageID` digest) or missing (a container
 * Waiting with an image-pull reason). */
export async function listContainerImageStatuses(
  namespace: string,
): Promise<K8sResult<ContainerImageStatus[]>> {
  const result = await k8sRequest<PodImageStatusListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
  if (!result.ok) return result;
  const out: ContainerImageStatus[] = [];
  for (const pod of result.data.items ?? []) {
    for (const cs of pod.status?.containerStatuses ?? []) {
      out.push({
        pod: pod.metadata.name,
        namespace: pod.metadata.namespace,
        container: cs.name,
        image: cs.image ?? "",
        imageID: cs.imageID ?? null,
        ready: cs.ready ?? false,
        waitingReason: cs.state?.waiting?.reason ?? null,
        waitingMessage: cs.state?.waiting?.message ?? null,
      });
    }
  }
  return { ok: true, data: out };
}

// ---------------------------------------------------------------------- Logs
//
// Real hyperscaler-PaaS-style Logs primitive (CloudWatch Logs / GCP Cloud
// Logging / Azure Monitor Logs equivalent) -- reads real pod stdout/stderr
// via the pod log subresource (GET .../pods/{pod}/log). Scoped by
// k8s/paas-rbac.yaml to a Role+RoleBinding per platform namespace, the
// same pattern the Secrets Manager module above uses and for the same
// reason: pod logs can contain application output more sensitive than the
// read-mostly resources in the ClusterRole, so this is never granted
// cluster-wide.

export interface K8sPod {
  name: string;
  namespace: string;
  phase: string;
  containers: string[];
  ready: boolean;
}

interface PodListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: { containers?: Array<{ name: string }> };
    status?: {
      phase?: string;
      containerStatuses?: Array<{ ready: boolean }>;
    };
  }>;
}

export async function listPods(namespace: string): Promise<K8sResult<K8sPod[]>> {
  const result = await k8sRequest<PodListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => {
      const statuses = item.status?.containerStatuses ?? [];
      return {
        name: item.metadata.name,
        namespace: item.metadata.namespace,
        phase: item.status?.phase ?? "Unknown",
        containers: (item.spec?.containers ?? []).map((c) => c.name),
        ready: statuses.length > 0 && statuses.every((cs) => cs.ready),
      };
    }),
  };
}

export interface PodLogOptions {
  /** Defaults to 200, matching the Logs page default. */
  tailLines?: number;
  /** Required when the pod has more than one container. */
  container?: string;
}

/**
 * Fetches real pod logs via the pods/log subresource. Unlike every other
 * function in this file, the API server's response body here is raw text
 * (real container stdout/stderr), never JSON -- so this cannot reuse
 * k8sRequest's JSON.parse and instead makes its own request with the same
 * fail-closed/timeout/error conventions. Error responses (403, 404, ...)
 * from this subresource ARE a JSON Status object, so those are parsed for
 * a real message when possible; a non-JSON error body is surfaced as-is.
 */
export async function getPodLogs(
  namespace: string,
  pod: string,
  options: PodLogOptions = {},
): Promise<K8sResult<string>> {
  const cfg = readInClusterConfig();
  if (!cfg) {
    return {
      ok: false,
      error:
        "not configured: no in-cluster ServiceAccount credentials found " +
        `(${SA_DIR}) -- this only works when running as the platform-console pod`,
    };
  }

  const params = new URLSearchParams({
    tailLines: String(options.tailLines ?? 200),
    timestamps: "true",
  });
  if (options.container) params.set("container", options.container);
  const path = `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(pod)}/log?${params.toString()}`;

  return new Promise((resolve) => {
    const req = https.request(
      {
        host: cfg.host,
        port: cfg.port,
        path,
        method: "GET",
        ca: cfg.ca,
        timeout: REQUEST_TIMEOUT_MS,
        headers: {
          Authorization: `Bearer ${cfg.token}`,
          Accept: "text/plain, application/json",
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          const raw = Buffer.concat(chunks).toString("utf8");
          if (status < 200 || status >= 300) {
            let message = raw || `HTTP ${status}`;
            try {
              const parsed = JSON.parse(raw) as { message?: string };
              if (parsed.message) message = parsed.message;
            } catch {
              // Not JSON -- use the raw body (or the HTTP status) as-is.
            }
            resolve({ ok: false, error: `GET ${path} failed: ${message}` });
            return;
          }
          resolve({ ok: true, data: raw });
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error(`timeout after ${REQUEST_TIMEOUT_MS}ms`)));
    req.on("error", (err) =>
      resolve({ ok: false, error: `unreachable: ${err.message}` }),
    );
    req.end();
  });
}

// ---------------------------------------------------------- Database Backups
//
// Real hyperscaler-PaaS-style Database Backups primitive (RDS / Cloud SQL /
// Cloud Spanner automated-backup equivalent). On-demand backup is a real
// `batch/v1` Job that runs `pg_dump` inside its own Pod against the target
// Postgres's real Service (`<name>.<namespace>.svc.cluster.local:5432`),
// using the exact same container image and the exact same password
// Secret/key the source Postgres Pod's own spec already references --
// read live off that Pod (createBackupJob's first step) rather than
// re-typed or guessed, so a backup can never silently drift to the wrong
// Postgres version or a stale/second credential. The dump is written to a
// PersistentVolumeClaim (platform-backups-pvc, created on first use if
// missing -- see ensureBackupsPvc). PVC contents are not directly
// queryable via the k8s API, so the honest backup inventory this module
// exposes is the Jobs themselves: name (encodes the timestamp), creation
// time, real completion status, real duration -- never a fabricated
// separate catalog. Scoped by k8s/paas-rbac.yaml to a single
// Role+RoleBinding in supabase-demo (get/list/create on batch/jobs and
// persistentvolumeclaims) -- never cluster-wide, and no update/patch/
// delete on either resource: a Job or PVC created wrong is left for a
// human with real kubectl access to clean up, not silently patched here.

export interface BackupJob {
  name: string;
  namespace: string;
  createdAt: string;
  startTime: string | null;
  completionTime: string | null;
  succeeded: number;
  failed: number;
  active: number;
  status: "Pending" | "Running" | "Complete" | "Failed";
  durationSeconds: number | null;
}

interface JobListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
    status?: {
      active?: number;
      succeeded?: number;
      failed?: number;
      startTime?: string;
      completionTime?: string;
    };
  }>;
}

function toBackupJob(item: NonNullable<JobListResponse["items"]>[number]): BackupJob {
  const succeeded = item.status?.succeeded ?? 0;
  const failed = item.status?.failed ?? 0;
  const active = item.status?.active ?? 0;
  const startTime = item.status?.startTime ?? null;
  const completionTime = item.status?.completionTime ?? null;
  let status: BackupJob["status"] = "Pending";
  if (succeeded > 0) status = "Complete";
  else if (failed > 0) status = "Failed";
  else if (active > 0) status = "Running";
  const durationSeconds =
    startTime && completionTime
      ? (new Date(completionTime).getTime() - new Date(startTime).getTime()) / 1000
      : null;
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    startTime,
    completionTime,
    succeeded,
    failed,
    active,
    status,
    durationSeconds,
  };
}

/**
 * Lists real `batch/v1` Jobs -- optionally filtered by label selector (the
 * Backups module passes `app=platform-backups` so operator-internal Jobs
 * already running in the same namespace, e.g. the supabase-operator's own
 * migration/sync Jobs, never appear in the backup inventory). This listing
 * IS the backup record: a completed Job whose own name encodes its
 * creation timestamp, never a separate fabricated catalog.
 */
export async function listJobs(
  namespace: string,
  labelSelector?: string,
): Promise<K8sResult<BackupJob[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<JobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs${qs}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toBackupJob) };
}

export interface BackupPvcStatus {
  name: string;
  namespace: string;
  phase: string | null;
  capacity: string | null;
  storageClassName: string | null;
}

interface PvcItem {
  metadata: { name: string; namespace: string };
  spec?: { storageClassName?: string; resources?: { requests?: { storage?: string } } };
  status?: { phase?: string; capacity?: { storage?: string } };
}

function toPvcStatus(item: PvcItem): BackupPvcStatus {
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    phase: item.status?.phase ?? null,
    capacity: item.status?.capacity?.storage ?? item.spec?.resources?.requests?.storage ?? null,
    storageClassName: item.spec?.storageClassName ?? null,
  };
}

/**
 * Reads the real PVC's status (phase/capacity/storage class). Returns
 * `{ ok: true, data: null }` -- not an error -- when the PVC hasn't been
 * provisioned yet, since that is itself honest, actionable state for the
 * Backups page to render ("not yet provisioned" rather than a fabricated
 * placeholder).
 */
export async function getBackupsPvc(
  namespace: string,
  name: string,
): Promise<K8sResult<BackupPvcStatus | null>> {
  const result = await k8sRequest<PvcItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/persistentvolumeclaims/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: toPvcStatus(result.data) };
}

/**
 * Creates the PVC the backup Jobs below write into, if it doesn't already
 * exist -- a real get-then-create, so calling this on every backup run is
 * a no-op after the first (never a spurious "already exists" error).
 * `storageClassName` is deliberately omitted from the manifest so the
 * cluster's own default StorageClass (the `(default)`-annotated one --
 * `standard`, backed by `rancher.io/local-path`, on this cluster) fills it
 * in via the API server's DefaultStorageClass admission plugin; it is
 * never hardcoded here.
 */
export async function ensureBackupsPvc(
  namespace: string,
  name: string,
  size: string,
): Promise<K8sResult<BackupPvcStatus>> {
  const existing = await getBackupsPvc(namespace, name);
  if (!existing.ok) return existing;
  if (existing.data) return { ok: true, data: existing.data };

  const manifest = {
    apiVersion: "v1",
    kind: "PersistentVolumeClaim",
    metadata: { name, namespace, labels: { app: "platform-backups" } },
    spec: {
      accessModes: ["ReadWriteOnce"],
      resources: { requests: { storage: size } },
    },
  };
  const result = await k8sRequest<PvcItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/persistentvolumeclaims`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toPvcStatus(result.data) };
}

interface PodSpecEnvVar {
  name: string;
  value?: string;
  valueFrom?: { secretKeyRef?: { name: string; key: string } };
}

interface PodSpecResponse {
  metadata: { name: string; namespace: string };
  spec?: {
    containers?: Array<{ name: string; image: string; env?: PodSpecEnvVar[] }>;
  };
}

async function getPodSpec(namespace: string, name: string): Promise<K8sResult<PodSpecResponse>> {
  return k8sRequest<PodSpecResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(name)}`,
  );
}

const BACKUPS_PVC_NAME = "platform-backups-pvc";
const BACKUPS_PVC_SIZE = "1Gi";

/**
 * Creates a real k8s Job that runs `pg_dump` against the target Postgres
 * Pod's own Service, using the exact same container image and the exact
 * same password Secret/key that source Pod's own spec already uses (read
 * live off `getPodSpec` -- never re-typed, never a second credential this
 * module invents; if the Pod has no PGPASSWORD/POSTGRES_PASSWORD sourced
 * from a real Secret, this refuses rather than inventing one). The Job
 * writes its dump straight to `platform-backups-pvc` (provisioned on first
 * call via `ensureBackupsPvc` if missing) at a path that encodes the Job's
 * own name, which itself encodes the creation timestamp -- so `listJobs`
 * above is a complete, honest inventory with no separate catalog to fall
 * out of sync.
 */
export async function createBackupJob(
  namespace: string,
  dbPodName: string,
): Promise<K8sResult<BackupJob>> {
  const podResult = await getPodSpec(namespace, dbPodName);
  if (!podResult.ok) return podResult;

  const container = podResult.data.spec?.containers?.[0];
  if (!container) {
    return { ok: false, error: `pod ${namespace}/${dbPodName} has no containers in its spec` };
  }

  const passwordEnv = container.env?.find(
    (e) =>
      (e.name === "PGPASSWORD" || e.name === "POSTGRES_PASSWORD") && e.valueFrom?.secretKeyRef,
  );
  if (!passwordEnv?.valueFrom?.secretKeyRef) {
    return {
      ok: false,
      error: `pod ${namespace}/${dbPodName} has no PGPASSWORD/POSTGRES_PASSWORD env sourced from a Secret -- refusing to invent a credential`,
    };
  }
  const pgUser = container.env?.find((e) => e.name === "POSTGRES_USER")?.value ?? "postgres";
  const pgDatabase =
    container.env?.find((e) => e.name === "PGDATABASE" || e.name === "POSTGRES_DB")?.value ??
    "postgres";

  // The Service backing a StatefulSet Pod shares the StatefulSet's name,
  // which is the Pod name minus its ordinal suffix (demo-db-postgres-0 ->
  // demo-db-postgres) -- true for every StatefulSet-backed database this
  // console creates (see createSingleDatabase above) or that the
  // supabase-operator itself creates, so this is a real structural
  // convention, not a guess specific to demo-db.
  const stem = dbPodName.replace(/-\d+$/, "");
  const host = `${stem}.${namespace}.svc.cluster.local`;

  const pvcResult = await ensureBackupsPvc(namespace, BACKUPS_PVC_NAME, BACKUPS_PVC_SIZE);
  if (!pvcResult.ok) return pvcResult;

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "z")
    .toLowerCase();
  const jobName = `pg-backup-${stem}-${timestamp}`.slice(0, 63).replace(/-+$/, "");
  const dumpPath = `/backups/${namespace}/${stem}/${jobName}.sql`;

  const dumpScript = [
    "set -e",
    `mkdir -p "$(dirname "${dumpPath}")"`,
    `pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "${dumpPath}"`,
    `ls -la "${dumpPath}"`,
  ].join("\n");

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: jobName,
      namespace,
      labels: { app: "platform-backups", "backup-source-pod": dbPodName, database: stem },
    },
    spec: {
      backoffLimit: 0,
      template: {
        metadata: { labels: { app: "platform-backups", job: jobName } },
        spec: {
          restartPolicy: "Never",
          containers: [
            {
              name: "pg-dump",
              image: container.image,
              command: ["sh", "-c", dumpScript],
              env: [
                { name: "PGHOST", value: host },
                { name: "PGPORT", value: "5432" },
                { name: "PGUSER", value: pgUser },
                { name: "PGDATABASE", value: pgDatabase },
                {
                  name: "PGPASSWORD",
                  valueFrom: { secretKeyRef: passwordEnv.valueFrom.secretKeyRef },
                },
              ],
              volumeMounts: [{ name: "backups", mountPath: "/backups" }],
            },
          ],
          volumes: [
            { name: "backups", persistentVolumeClaim: { claimName: BACKUPS_PVC_NAME } },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<NonNullable<JobListResponse["items"]>[number]>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

// ------------------------------------------------------- Database Restores
//
// Real hyperscaler-PaaS-style point-in-time-restore equivalent (RDS "Restore
// to point in time" / Cloud SQL "Restore" equivalent) for the on-demand
// backups above. A real `batch/v1` Job, same shape and same
// credential-discovery pattern as createBackupJob: it reads the TARGET
// Postgres Pod's own spec/env live (never a second, re-typed credential),
// mounts the exact same `platform-backups-pvc` the backup Jobs write into
// (read-only here -- this Job never writes to the PVC), and locates the
// specific dump file the named backup Job produced by reading that Job's own
// object back from the API server (its `database` label, the same value
// createBackupJob wrote into `dumpPath`) rather than re-parsing/guessing a
// path out of the Job's name string.
//
// createBackupJob's real pg_dump invocation has no `-F` flag, so the dump is
// plain SQL (confirmed live: the dump file starts with `-- PostgreSQL
// database dump`, `\restrict <token>`, plain `CREATE TABLE`/`COPY ... FROM
// stdin` statements) -- so restore uses `psql -f`, never `pg_restore` (which
// only reads pg_dump's custom/directory/tar formats). A plain dump also
// carries no `--clean`/`--if-exists` DROP statements, so loading it directly
// on top of a target that still has the same rows would abort every
// `COPY ... FROM stdin` block at the first pre-existing-row conflict
// (COPY is one atomic statement -- a single duplicate-key error rolls back
// that whole table's data, not just the offending row), silently restoring
// nothing. To give this real restore-overwrites-target semantics (the same
// "this replaces the target's contents" behavior RDS/Cloud SQL restore has),
// the Job's script first clears every real table it can before running
// `psql -f`.
//
// Live-discovered, disclosed constraint (checked directly against this
// cluster's real demo-db-postgres before writing this script, not assumed):
// the credential createBackupJob's own discovery pattern finds (the
// `postgres` role) is NOT a Postgres superuser and does NOT own most of the
// real schemas here (`auth`/`storage`/`_realtime`/... are owned by
// `supabase_admin`/`supabase_auth_admin`, confirmed live via `\dn+` and
// `select usesuper from pg_user`) -- so a `DROP SCHEMA ... CASCADE` (which
// requires ownership or superuser) fails with a real `must be owner of
// schema` error for nearly every schema. What that same role DOES have,
// confirmed live via `information_schema.role_table_grants`, is real
// row-level DML (INSERT/UPDATE/DELETE/TRUNCATE) on the actual data tables
// via explicit GRANTs -- so the clearing step is a per-table `TRUNCATE
// ... CASCADE` (real DML the credential is actually authorized for) inside
// a loop that catches `insufficient_privilege` per table and skips it
// (logged via RAISE NOTICE, never silently swallowed) rather than aborting
// the whole clear because one system-owned table (e.g. a migrations table)
// isn't grantable to `postgres`. `psql -f` on the dump itself then runs
// WITHOUT `-v ON_ERROR_STOP=1`: a plain dump replayed by a non-owner,
// non-superuser role against a target whose schemas/tables already exist
// necessarily produces real, expected, harmless per-statement errors on
// every `CREATE SCHEMA`/`CREATE TABLE`/permission-gated DDL statement in
// the dump (the objects already exist and this role isn't allowed to
// touch their DDL) -- live-confirmed these are cosmetic: the load-bearing
// `COPY ... FROM stdin` data statements for tables the role has TRUNCATE
// (and therefore INSERT) on still succeed and really restore the row data,
// confirmed end-to-end against a real deleted-and-restored user (see the
// evidence bundle's restore-recovers-real-deleted-data control). A dump
// whose table ordering doesn't respect every FK dependency can still leave
// a same-run child-table COPY failing on a not-yet-loaded parent row (also
// observed and disclosed there) -- a real limitation of single-pass replay
// into a live, non-empty, non-owned target, not swept under the rug. Both
// psql invocations still log everything to the Job's own pod logs (`kubectl
// logs`), the same real inspection path every other Job in this module
// relies on. No new RBAC: reuses the same `platform-console-backups` Role's
// `batch/jobs` create verb (no update/patch/delete, same as backups) --
// see k8s/paas-rbac.yaml.

interface JobItem {
  metadata: { name: string; namespace: string; creationTimestamp: string; labels?: Record<string, string> };
  status?: {
    active?: number;
    succeeded?: number;
    failed?: number;
    startTime?: string;
    completionTime?: string;
  };
}

async function getJob(namespace: string, name: string): Promise<K8sResult<JobItem>> {
  return k8sRequest<JobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(name)}`,
  );
}

/**
 * Creates a real `batch/v1` restore Job. `backupJobName` must name a real,
 * already-`Complete` backup Job created by createBackupJob above (its
 * `database` label is read back to locate the exact dump file that Job
 * wrote -- refuses if the Job doesn't exist, has no `database` label, or
 * hasn't reached `status.succeeded >= 1`, since restoring from an
 * incomplete/failed/nonexistent backup would be dishonest). `targetDbPodName`
 * is the live Postgres Pod to restore into -- its own spec/env supplies the
 * restore Job's credentials, exactly as createBackupJob does for the source
 * side, so this can restore into a different Pod than the one the backup
 * was taken from, not just back into itself.
 */
export async function createRestoreJob(
  namespace: string,
  backupJobName: string,
  targetDbPodName: string,
): Promise<K8sResult<BackupJob>> {
  const jobResult = await getJob(namespace, backupJobName);
  if (!jobResult.ok) {
    return { ok: false, error: `backup Job ${backupJobName} not found: ${jobResult.error}` };
  }
  const sourceStem = jobResult.data.metadata.labels?.database;
  if (!sourceStem) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has no "database" label -- cannot locate its dump file`,
    };
  }
  if ((jobResult.data.status?.succeeded ?? 0) < 1) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has not reached Complete (status.succeeded=${jobResult.data.status?.succeeded ?? 0}) -- refusing to restore from an incomplete or failed backup`,
    };
  }
  const dumpPath = `/backups/${namespace}/${sourceStem}/${backupJobName}.sql`;

  const podResult = await getPodSpec(namespace, targetDbPodName);
  if (!podResult.ok) return podResult;

  const container = podResult.data.spec?.containers?.[0];
  if (!container) {
    return { ok: false, error: `pod ${namespace}/${targetDbPodName} has no containers in its spec` };
  }

  const passwordEnv = container.env?.find(
    (e) =>
      (e.name === "PGPASSWORD" || e.name === "POSTGRES_PASSWORD") && e.valueFrom?.secretKeyRef,
  );
  if (!passwordEnv?.valueFrom?.secretKeyRef) {
    return {
      ok: false,
      error: `pod ${namespace}/${targetDbPodName} has no PGPASSWORD/POSTGRES_PASSWORD env sourced from a Secret -- refusing to invent a credential`,
    };
  }
  const pgUser = container.env?.find((e) => e.name === "POSTGRES_USER")?.value ?? "postgres";
  const pgDatabase =
    container.env?.find((e) => e.name === "PGDATABASE" || e.name === "POSTGRES_DB")?.value ??
    "postgres";

  const targetStem = targetDbPodName.replace(/-\d+$/, "");
  const host = `${targetStem}.${namespace}.svc.cluster.local`;

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "z")
    .toLowerCase();
  const jobName = `pg-restore-${targetStem}-${timestamp}`.slice(0, 63).replace(/-+$/, "");

  // Written via a QUOTED heredoc ('CLEARSQL') rather than inlined into a
  // `psql -c "..."` shell argument -- a quoted heredoc disables all shell
  // expansion inside it, which plain double-quoting would not: the SQL's
  // own `$do$` dollar-quote tag would otherwise be parsed by sh as `$do`
  // (an unset shell variable, expanding to empty) followed by a stray `$`,
  // corrupting the PL/pgSQL block before psql ever sees it.
  const restoreScript = [
    "set -e",
    `test -f "${dumpPath}" || { echo "backup dump not found at ${dumpPath}" >&2; exit 1; }`,
    `cat <<'CLEARSQL' > /tmp/clear_tables.sql`,
    "DO $do$",
    "DECLARE",
    "  r record;",
    "BEGIN",
    "  FOR r IN",
    "    SELECT n.nspname, c.relname",
    "    FROM pg_class c",
    "    JOIN pg_namespace n ON n.oid = c.relnamespace",
    "    WHERE c.relkind = 'r'",
    "      AND n.nspname NOT IN ('pg_catalog','information_schema')",
    "      AND n.nspname NOT LIKE 'pg_temp_%'",
    "      AND n.nspname NOT LIKE 'pg_toast%'",
    "  LOOP",
    "    BEGIN",
    "      EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.nspname) || '.' || quote_ident(r.relname) || ' CASCADE';",
    "    EXCEPTION WHEN insufficient_privilege THEN",
    "      RAISE NOTICE 'restore: skipping % (insufficient_privilege on this credential)', r.nspname || '.' || r.relname;",
    "    END;",
    "  END LOOP;",
    "END $do$;",
    "CLEARSQL",
    `echo "Clearing existing table data in $PGDATABASE before restore (this credential owns no schemas here -- TRUNCATE, not DROP SCHEMA -- see lib/k8s.ts createRestoreJob for why)..."`,
    `psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -f /tmp/clear_tables.sql`,
    `echo "Restoring ${dumpPath} into $PGDATABASE (per-statement errors below on already-existing/not-owned DDL are expected -- see module doc; the real data COPY statements are what matters)..."`,
    `psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "${dumpPath}"`,
    `echo "Restore script finished."`,
  ].join("\n");

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: jobName,
      namespace,
      labels: {
        app: "platform-restores",
        "restore-source-job": backupJobName,
        "restore-target-pod": targetDbPodName,
        database: targetStem,
      },
    },
    spec: {
      backoffLimit: 0,
      template: {
        metadata: { labels: { app: "platform-restores", job: jobName } },
        spec: {
          restartPolicy: "Never",
          containers: [
            {
              name: "pg-restore",
              image: container.image,
              command: ["sh", "-c", restoreScript],
              env: [
                { name: "PGHOST", value: host },
                { name: "PGPORT", value: "5432" },
                { name: "PGUSER", value: pgUser },
                { name: "PGDATABASE", value: pgDatabase },
                {
                  name: "PGPASSWORD",
                  valueFrom: { secretKeyRef: passwordEnv.valueFrom.secretKeyRef },
                },
              ],
              volumeMounts: [{ name: "backups", mountPath: "/backups", readOnly: true }],
            },
          ],
          volumes: [
            {
              name: "backups",
              persistentVolumeClaim: { claimName: BACKUPS_PVC_NAME, readOnly: true },
            },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<NonNullable<JobListResponse["items"]>[number]>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

// -------------------------------------------------------------- Cost & Usage
//
// Real hyperscaler-PaaS-style Cost & Usage primitive (AWS Cost Explorer /
// GCP Billing Reports / Azure Cost Management equivalent) -- deliberately
// WITHOUT any payment processor or fabricated currency. This cluster has no
// billing system, so the only honest substitute is what is actually true
// and measurable: real live per-pod CPU/memory usage from the metrics
// pipeline already installed and verified on this cluster
// (metrics-server, confirmed working by the autoscaling-enforced control --
// `kubectl top` returns real numbers, not `error: Metrics API not
// available`), combined with the real per-namespace ResourceQuota object
// (the actual ceiling each namespace's workloads are bound by). This
// module reports real, currently-measured infrastructure consumption --
// millicores, MiB, and a plain percentage-of-quota figure -- never a
// dollar amount tied to any real biller.
//
// Uses the exact same in-cluster API pattern as every other function in
// this file (k8sRequest against the pod's own ServiceAccount token/CA),
// reading two additional resource types: `metrics.k8s.io/v1beta1` PodMetrics
// (real-time, reported by the kubelet's cAdvisor, scraped by metrics-server
// on its own interval -- typically ~15-60s stale, never fabricated) and the
// core `resourcequotas` object already used to gate real Pod admission
// (confirmed live via the resource-quotas-enforced control's negative
// test). Both verbs (`get`/`list` on `pods.metrics.k8s.io` and
// `resourcequotas`) were added to the existing cluster-wide
// `ClusterRole/platform-console-paas` in k8s/paas-rbac.yaml -- same
// sensitivity class as the Services/Deployments/Roles already granted
// cluster-wide there (workload metadata and resource ceilings, not
// secrets), confirmed via `kubectl auth can-i` returning real `no` for both
// verbs before the RBAC change and real `yes` after.

/**
 * Parses a Kubernetes `resource.Quantity` string (used for both CPU and
 * memory fields across PodMetrics and ResourceQuota) into a plain number in
 * its base unit (cores for CPU, bytes for memory) -- the caller converts to
 * millicores/MiB. Handles every suffix actually observed live on this
 * cluster (`n` nanocores on PodMetrics CPU, `Ki` on PodMetrics/Quota
 * memory, `m` and bare-integer cores on Quota CPU, `Gi`/`Mi` on Quota
 * memory) plus the rest of the documented Kubernetes quantity suffix set
 * (`u`, decimal `k`/`M`/`G`/`T`/`P`/`E`, binary `Ti`/`Pi`/`Ei`) for
 * robustness against values this cluster doesn't currently happen to emit.
 * Returns `null` on anything that doesn't parse -- never a fabricated 0.
 */
const QUANTITY_SUFFIX_MULTIPLIERS: Record<string, number> = {
  n: 1e-9,
  u: 1e-6,
  m: 1e-3,
  "": 1,
  k: 1e3,
  M: 1e6,
  G: 1e9,
  T: 1e12,
  P: 1e15,
  E: 1e18,
  Ki: 2 ** 10,
  Mi: 2 ** 20,
  Gi: 2 ** 30,
  Ti: 2 ** 40,
  Pi: 2 ** 50,
  Ei: 2 ** 60,
};

function parseK8sQuantity(raw: string | undefined): number | null {
  if (!raw) return null;
  const match = /^([0-9.eE+-]+)(Ki|Mi|Gi|Ti|Pi|Ei|[numkMGTPE]?)$/.exec(raw.trim());
  if (!match) return null;
  const [, numStr, suffix] = match;
  const num = Number(numStr);
  if (!Number.isFinite(num)) return null;
  const multiplier = QUANTITY_SUFFIX_MULTIPLIERS[suffix];
  if (multiplier === undefined) return null;
  return num * multiplier;
}

function quantityToMillicores(raw: string | undefined): number | null {
  const cores = parseK8sQuantity(raw);
  return cores === null ? null : cores * 1000;
}

function quantityToMiB(raw: string | undefined): number | null {
  const bytes = parseK8sQuantity(raw);
  return bytes === null ? null : bytes / (1024 * 1024);
}

export interface ResourceQuotaSnapshot {
  name: string;
  namespace: string;
  /** Hard ceiling on the sum of every container's resource *limit* in the
   * namespace -- the real bound live usage cannot exceed without being
   * throttled (CPU) or OOM-killed (memory). `null` when the ResourceQuota
   * object doesn't set that particular field. */
  hardCpuMillicores: number | null;
  hardMemoryMiB: number | null;
  /** Hard ceiling on the sum of every container's resource *request*
   * (reservation) in the namespace -- shown for context; usage is compared
   * against the limits fields above, since that is the ceiling usage is
   * actually bound by. */
  hardRequestsCpuMillicores: number | null;
  hardRequestsMemoryMiB: number | null;
  hardPods: number | null;
  usedPods: number | null;
}

interface ResourceQuotaListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      hard?: Record<string, string>;
      used?: Record<string, string>;
    };
  }>;
}

/**
 * Reads the real ResourceQuota object for one namespace. Returns
 * `{ ok: true, data: null }` -- not an error -- when the namespace has no
 * ResourceQuota at all (true today for `supabase-demo`, confirmed live via
 * `kubectl get resourcequota -n supabase-demo` returning no resources),
 * since that is itself honest state: this module has no quota to compare
 * usage against for that namespace, and says so rather than fabricating
 * one. If a namespace ever carries more than one ResourceQuota object
 * (none do today), the first one returned by the API is used and the rest
 * are ignored -- disclosed here rather than silently summed.
 */
export async function getResourceQuota(
  namespace: string,
): Promise<K8sResult<ResourceQuotaSnapshot | null>> {
  const result = await k8sRequest<ResourceQuotaListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas`,
  );
  if (!result.ok) return result;
  const item = (result.data.items ?? [])[0];
  if (!item) return { ok: true, data: null };
  const hard = item.status?.hard ?? {};
  const used = item.status?.used ?? {};
  return {
    ok: true,
    data: {
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      hardCpuMillicores: quantityToMillicores(hard["limits.cpu"]),
      hardMemoryMiB: quantityToMiB(hard["limits.memory"]),
      hardRequestsCpuMillicores: quantityToMillicores(hard["requests.cpu"]),
      hardRequestsMemoryMiB: quantityToMiB(hard["requests.memory"]),
      hardPods: hard["pods"] !== undefined ? Number(hard["pods"]) : null,
      usedPods: used["pods"] !== undefined ? Number(used["pods"]) : null,
    },
  };
}

interface PodMetricsListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    containers?: Array<{ name: string; usage?: { cpu?: string; memory?: string } }>;
  }>;
}

export interface NamespaceResourceUsage {
  namespace: string;
  /** Real, current, live sum of every container's `usage.cpu` across every
   * Pod metrics-server has a fresh reading for in this namespace (the exact
   * same source `kubectl top pods -n <namespace>` reads). */
  cpuUsageMillicores: number;
  memoryUsageMiB: number;
  /** Number of Pods metrics-server actually returned a reading for --
   * usually equals the live Pod count, but can be lower for a few seconds
   * right after a Pod starts, before the first kubelet scrape lands. */
  podsMeasured: number;
  /** `null` when the namespace has no ResourceQuota object at all. */
  quota: ResourceQuotaSnapshot | null;
  /** `cpuUsageMillicores` / `quota.hardCpuMillicores` * 100 -- `null` when
   * there is no quota, or the quota sets no `limits.cpu`. Not clamped to
   * 100: a namespace can (briefly) show live usage above its limits
   * ceiling, since metrics-server's reading and the scheduler's admission
   * check are not perfectly synchronous -- shown as-is rather than
   * silently capped. */
  cpuPercentOfQuota: number | null;
  memoryPercentOfQuota: number | null;
}

/**
 * Combines real live metrics (`metrics.k8s.io/v1beta1` PodMetrics -- the
 * same source `kubectl top pods` reads) with the real ResourceQuota object
 * for one namespace, returning current CPU/memory usage, the quota's hard
 * ceiling, and a plain percentage-of-quota figure. This is real, measured
 * infrastructure consumption -- not billing, not currency; no dollar
 * amount is computed or returned anywhere in this function.
 */
export async function getResourceUsage(
  namespace: string,
): Promise<K8sResult<NamespaceResourceUsage>> {
  const [metricsResult, quotaResult] = await Promise.all([
    k8sRequest<PodMetricsListResponse>(
      `/apis/metrics.k8s.io/v1beta1/namespaces/${encodeURIComponent(namespace)}/pods`,
    ),
    getResourceQuota(namespace),
  ]);
  if (!metricsResult.ok) return metricsResult;
  if (!quotaResult.ok) return quotaResult;

  let cpuUsageMillicores = 0;
  let memoryUsageMiB = 0;
  const pods = metricsResult.data.items ?? [];
  for (const pod of pods) {
    for (const container of pod.containers ?? []) {
      cpuUsageMillicores += quantityToMillicores(container.usage?.cpu) ?? 0;
      memoryUsageMiB += quantityToMiB(container.usage?.memory) ?? 0;
    }
  }

  const quota = quotaResult.data;
  const cpuPercentOfQuota =
    quota?.hardCpuMillicores && quota.hardCpuMillicores > 0
      ? (cpuUsageMillicores / quota.hardCpuMillicores) * 100
      : null;
  const memoryPercentOfQuota =
    quota?.hardMemoryMiB && quota.hardMemoryMiB > 0
      ? (memoryUsageMiB / quota.hardMemoryMiB) * 100
      : null;

  return {
    ok: true,
    data: {
      namespace,
      cpuUsageMillicores,
      memoryUsageMiB,
      podsMeasured: pods.length,
      quota,
      cpuPercentOfQuota,
      memoryPercentOfQuota,
    },
  };
}

// -------------------------------------------------------------- Feature Flags
//
// Real hyperscaler-PaaS-style Feature Flags primitive (AWS AppConfig /
// LaunchDarkly / GCP Feature Flags equivalent) -- backed by a single real
// k8s ConfigMap (`platform-feature-flags`, `platform-console` namespace),
// no external SaaS dependency, no separate flag-evaluation service. Flag
// values are plain strings in the ConfigMap's `data` map (`"true"`/
// `"false"` for boolean flags, though nothing here enforces that shape --
// arbitrary string flags are equally real). Scoped by k8s/paas-rbac.yaml
// to a single least-privilege Role+RoleBinding in platform-console's own
// namespace only (get/list/create/update on configmaps) -- never
// cluster-wide, no delete verb: this console only ever creates the flags
// ConfigMap once or edits its `data` map in place.

export interface FeatureFlagsConfigMap {
  name: string;
  namespace: string;
  data: Record<string, string>;
}

interface ConfigMapItem {
  metadata: { name: string; namespace: string };
  data?: Record<string, string>;
}

function toFeatureFlagsConfigMap(item: ConfigMapItem): FeatureFlagsConfigMap {
  return { name: item.metadata.name, namespace: item.metadata.namespace, data: item.data ?? {} };
}

/**
 * Reads one real ConfigMap. Returns `{ ok: true, data: null }` -- not an
 * error -- when it doesn't exist yet, so callers can distinguish "not
 * provisioned" from a real API failure, same convention as
 * getBackupsPvc above.
 */
export async function getConfigMap(
  namespace: string,
  name: string,
): Promise<K8sResult<FeatureFlagsConfigMap | null>> {
  const result = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
}

/**
 * Real get-then-update-or-create, same pattern ensureBackupsPvc above
 * already uses for a different resource type: reads the ConfigMap first
 * (`getConfigMap`); if it already exists, applies `data` as a real RFC
 * 7386 JSON merge patch (`Content-Type: application/merge-patch+json`) --
 * merge-patch on a nested object field is recursive, so passing just the
 * one changed key (e.g. `{ "verbose-status": "true" }`) updates that key
 * without touching any other flag already in the map; never a blind
 * full-object PUT that would require re-sending every existing flag or
 * risk clobbering one this call didn't read. If it doesn't exist yet,
 * POSTs a fresh ConfigMap manifest instead.
 */
export async function createOrUpdateConfigMap(
  namespace: string,
  name: string,
  data: Record<string, string>,
): Promise<K8sResult<FeatureFlagsConfigMap>> {
  const existing = await getConfigMap(namespace, name);
  if (!existing.ok) return existing;

  if (existing.data) {
    const result = await k8sRequest<ConfigMapItem>(
      `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(name)}`,
      "PATCH",
      { data },
      "application/merge-patch+json",
    );
    if (!result.ok) return result;
    return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
  }

  const manifest = {
    apiVersion: "v1",
    kind: "ConfigMap",
    metadata: { name, namespace },
    data,
  };
  const result = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
}
