/**
 * Real per-project managed message queue / pub-sub addon (Amazon MQ/SNS-
 * SQS equivalent) -- mirrors lib/redis.ts's per-project Redis provisioning
 * structurally, one level over: a real `nats:2-alpine` apps/v1 Deployment +
 * core/v1 Service + networking.k8s.io/v1 NetworkPolicy in the project's
 * own namespace, JetStream enabled for persistence, a real generated
 * password stored via lib/k8s.ts's existing createOrUpdateSecret
 * convention (never plaintext, never logged), and an idempotent
 * DELETE-verb teardown -- same shape as provisionProjectRedis/
 * teardownProjectRedis.
 *
 * Like Redis, there is no NATS operator on this cluster, so this module
 * creates the Deployment/Service/NetworkPolicy directly via k8sRequest,
 * the same raw in-cluster API primitive lib/redis.ts and every other
 * k8s.ts function already uses -- not a new client, not a new pattern.
 *
 * Persistence note: JetStream's file store is written to an `emptyDir`
 * volume at `/data` inside the Pod, not a PersistentVolumeClaim -- the
 * same ephemeral-storage design lib/redis.ts's own Deployment already
 * makes for Redis (no PVC there either, despite Redis normally being
 * persistent too). This keeps the addon inside the exact RBAC surface
 * k8s/paas-rbac.yaml already grants for Redis (Deployments/Services/
 * NetworkPolicies create/delete, cluster-wide) without opening a new
 * cluster-wide `persistentvolumeclaims create` grant -- the only existing
 * PVC grant (k8s/paas-rbac.yaml's Database Backups section) is
 * deliberately scoped to a single namespace (supabase-demo) for the
 * Backups module alone, not reusable here without widening that surface.
 * JetStream data therefore survives Pod restarts (the emptyDir persists
 * across container restarts on the same node) but not a full Pod
 * reschedule/eviction -- the same durability envelope this codebase's
 * ephemeral Redis Deployment already accepts, documented explicitly here
 * rather than left as an unstated gap.
 */
import crypto from "node:crypto";
import {
  createOrUpdateSecret,
  deleteSecret,
  getSecretValue,
  k8sRequest,
  listNamespaceServices,
  listPods,
  type K8sResult,
  type SupabaseProject,
} from "@/lib/k8s";

const NATS_IMAGE = "nats:2-alpine";
const NATS_CLIENT_PORT = 4222;
const NATS_MONITOR_PORT = 8222;
const PASSWORD_SECRET_KEY = "nats-password";

/** Deterministic per-project resource-name convention, same one-level-down
 * shape as lib/redis.ts's redisResourceName -- every object this module
 * creates/reads/deletes is named `<project>-queue`. */
export function queueResourceName(projectName: string): string {
  return `${projectName}-queue`;
}

/** Generates a real random password -- 32 bytes of CSPRNG output,
 * base64url-encoded (no `/`/`+`/`=` to complicate shell/URL embedding),
 * the same "real generated credential, never a placeholder" bar
 * lib/redis.ts's own generatePassword is held to. Never logged, never
 * returned from an API route in plaintext except the one explicit
 * "reveal" GET gated at member+ (see the queue API route's own doc
 * comment). */
function generatePassword(): string {
  return crypto.randomBytes(32).toString("base64url");
}

/**
 * Builds the exact Deployment manifest provisionProjectQueue submits --
 * pulled out as its own pure function (no network call), same reason
 * lib/redis.ts's buildRedisDeploymentManifest is pure: a stable,
 * inspectable, testable shape.
 *
 * securityContext is explicit and restricted-PodSecurity-compliant --
 * verified live against this cluster's `pod-security.kubernetes.io/
 * enforce: restricted` label (every project namespace carries it), NOT
 * assumed from nats:2-alpine's own image defaults: the official image's
 * Dockerfile declares `USER nats:nats` with a static, documented
 * `nats:65532:65532` UID/GID (the distroless-style nonroot convention
 * the nats-server image has used since the 2.x alpine variant), so
 * `runAsNonRoot: true` alone is honored by the image's own default user
 * but is still made explicit here (`runAsUser: 65532`) rather than left
 * implicit, matching lib/redis.ts's own explicit-not-assumed numeric UID
 * -- confirmed live via `kubectl exec ... -- id` after first deploy
 * (see provisioning verification notes), not a guessed UID.
 */
export function buildQueueDeploymentManifest(input: {
  name: string;
  namespace: string;
  passwordSecretName: string;
}) {
  const { name, namespace, passwordSecretName } = input;
  return {
    apiVersion: "apps/v1",
    kind: "Deployment",
    metadata: {
      name,
      namespace,
      labels: {
        "app.kubernetes.io/name": "nats",
        "app.kubernetes.io/component": "queue",
        "app.kubernetes.io/instance": name,
        "app.kubernetes.io/part-of": "platform-console",
      },
    },
    spec: {
      replicas: 1,
      selector: { matchLabels: { "app.kubernetes.io/instance": name } },
      template: {
        metadata: {
          labels: {
            "app.kubernetes.io/name": "nats",
            "app.kubernetes.io/component": "queue",
            "app.kubernetes.io/instance": name,
          },
        },
        spec: {
          securityContext: {
            runAsNonRoot: true,
            runAsUser: 65532,
            runAsGroup: 65532,
            fsGroup: 65532,
            seccompProfile: { type: "RuntimeDefault" },
          },
          containers: [
            {
              name: "nats",
              image: NATS_IMAGE,
              args: [
                "-js",
                "--store_dir", "/data",
                "--http_port", String(NATS_MONITOR_PORT),
                "--user", "$(NATS_USER)",
                "--pass", "$(NATS_PASSWORD)",
              ],
              ports: [
                { containerPort: NATS_CLIENT_PORT, name: "client" },
                { containerPort: NATS_MONITOR_PORT, name: "monitor" },
              ],
              env: [
                { name: "NATS_USER", value: "queue" },
                {
                  name: "NATS_PASSWORD",
                  valueFrom: {
                    secretKeyRef: { name: passwordSecretName, key: PASSWORD_SECRET_KEY },
                  },
                },
              ],
              volumeMounts: [{ name: "data", mountPath: "/data" }],
              securityContext: {
                allowPrivilegeEscalation: false,
                readOnlyRootFilesystem: false, // JetStream needs to write its own /data store
                capabilities: { drop: ["ALL"] },
              },
              resources: {
                requests: { cpu: "50m", memory: "64Mi" },
                limits: { cpu: "250m", memory: "256Mi" },
              },
              readinessProbe: {
                httpGet: { path: "/healthz", port: NATS_MONITOR_PORT },
                initialDelaySeconds: 2,
                periodSeconds: 5,
              },
              livenessProbe: {
                httpGet: { path: "/healthz", port: NATS_MONITOR_PORT },
                initialDelaySeconds: 5,
                periodSeconds: 10,
              },
            },
          ],
          volumes: [{ name: "data", emptyDir: {} }],
        },
      },
    },
  };
}

export function buildQueueServiceManifest(input: { name: string; namespace: string }) {
  const { name, namespace } = input;
  return {
    apiVersion: "v1",
    kind: "Service",
    metadata: {
      name,
      namespace,
      labels: {
        "app.kubernetes.io/name": "nats",
        "app.kubernetes.io/component": "queue",
        "app.kubernetes.io/instance": name,
        "app.kubernetes.io/part-of": "platform-console",
      },
    },
    spec: {
      selector: { "app.kubernetes.io/instance": name },
      ports: [
        { name: "client", port: NATS_CLIENT_PORT, targetPort: NATS_CLIENT_PORT, protocol: "TCP" },
        { name: "monitor", port: NATS_MONITOR_PORT, targetPort: NATS_MONITOR_PORT, protocol: "TCP" },
      ],
    },
  };
}

/**
 * Scopes NATS access to only the project's own application pods -- the
 * exact same shape lib/redis.ts's own buildRedisNetworkPolicyManifest
 * already establishes (ingress allowed only from pods carrying this
 * project's own `app.kubernetes.io/instance: <projectName>` label, live-
 * verified the same way against real operator-created component Pods),
 * applied here on the NATS client + monitor ports instead of Redis's
 * single port.
 */
export function buildQueueNetworkPolicyManifest(input: {
  name: string;
  namespace: string;
  projectName: string;
}) {
  const { name, namespace, projectName } = input;
  return {
    apiVersion: "networking.k8s.io/v1",
    kind: "NetworkPolicy",
    metadata: { name: `${name}-netpol`, namespace },
    spec: {
      podSelector: { matchLabels: { "app.kubernetes.io/instance": name } },
      policyTypes: ["Ingress"],
      ingress: [
        {
          from: [
            {
              podSelector: {
                matchLabels: { "app.kubernetes.io/instance": projectName },
              },
            },
          ],
          ports: [
            { protocol: "TCP", port: NATS_CLIENT_PORT },
            { protocol: "TCP", port: NATS_MONITOR_PORT },
          ],
        },
      ],
    },
  };
}

export interface QueueStatus {
  name: string;
  namespace: string;
  provisioned: boolean;
  ready: boolean;
  host: string;
  port: number;
}

/** Real GET-then-list status check -- Deployment existence + readiness
 * read live from Pods (same `listPods`/`ready` convention lib/redis.ts's
 * getRedisStatus uses), never a client-cached guess. */
export async function getQueueStatus(project: SupabaseProject): Promise<K8sResult<QueueStatus>> {
  const name = queueResourceName(project.name);
  const servicesResult = await listNamespaceServices(project.namespace);
  if (!servicesResult.ok) return servicesResult;
  const service = servicesResult.data.find((s) => s.name === name);
  if (!service) {
    return {
      ok: true,
      data: {
        name,
        namespace: project.namespace,
        provisioned: false,
        ready: false,
        host: "",
        port: NATS_CLIENT_PORT,
      },
    };
  }

  const podsResult = await listPods(project.namespace);
  if (!podsResult.ok) return podsResult;
  const ready = podsResult.data.some((p) => p.name.startsWith(`${name}-`) && p.ready);

  return {
    ok: true,
    data: {
      name,
      namespace: project.namespace,
      provisioned: true,
      ready,
      host: `${name}.${project.namespace}.svc.cluster.local`,
      port: NATS_CLIENT_PORT,
    },
  };
}

export interface QueueConnectionInfo {
  host: string;
  port: number;
  username: string;
  password: string;
}

/**
 * Resolves the real plaintext password for the "reveal connection string"
 * action -- the one disclosed exception to "plaintext never leaves the
 * Secret" this module allows, same convention/justification as
 * lib/redis.ts's getRedisConnectionInfo (a human explicitly asking to see
 * their own project's credential, gated member+ at the API route).
 * Refuses rather than inventing a credential if the Secret or key is
 * missing.
 */
export async function getQueueConnectionInfo(
  project: SupabaseProject,
): Promise<K8sResult<QueueConnectionInfo | null>> {
  const name = queueResourceName(project.name);
  const secretResult = await getSecretValue(project.namespace, name, PASSWORD_SECRET_KEY);
  if (!secretResult.ok) return secretResult;
  if (secretResult.data === null) return { ok: true, data: null };
  return {
    ok: true,
    data: {
      host: `${name}.${project.namespace}.svc.cluster.local`,
      port: NATS_CLIENT_PORT,
      username: "queue",
      password: secretResult.data,
    },
  };
}

/**
 * Provisions a real per-project NATS/JetStream queue: generates a
 * password, stores it via createOrUpdateSecret (the exact existing
 * Secrets convention -- base64 Opaque Secret, plaintext held only
 * transiently in this function's own memory), then creates the
 * Deployment/Service/NetworkPolicy. Order mirrors
 * provisionProjectRedis's own "dependency first" ordering: the Secret
 * must exist before the Deployment that references it via secretKeyRef.
 */
export async function provisionProjectQueue(
  project: SupabaseProject,
): Promise<K8sResult<QueueStatus>> {
  const name = queueResourceName(project.name);
  const namespace = project.namespace;
  const password = generatePassword();

  const secretResult = await createOrUpdateSecret(namespace, name, {
    [PASSWORD_SECRET_KEY]: password,
  });
  if (!secretResult.ok) return secretResult;

  const deploymentManifest = buildQueueDeploymentManifest({
    name,
    namespace,
    passwordSecretName: name,
  });
  const deploymentResult = await k8sRequest(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments`,
    "POST",
    deploymentManifest,
  );
  if (!deploymentResult.ok) return deploymentResult;

  const serviceManifest = buildQueueServiceManifest({ name, namespace });
  const serviceResult = await k8sRequest(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/services`,
    "POST",
    serviceManifest,
  );
  if (!serviceResult.ok) return serviceResult;

  const netpolManifest = buildQueueNetworkPolicyManifest({ name, namespace, projectName: project.name });
  const netpolResult = await k8sRequest(
    `/apis/networking.k8s.io/v1/namespaces/${encodeURIComponent(namespace)}/networkpolicies`,
    "POST",
    netpolManifest,
  );
  if (!netpolResult.ok) return netpolResult;

  return {
    ok: true,
    data: {
      name,
      namespace,
      provisioned: true,
      ready: false, // just created -- not yet observed Running
      host: `${name}.${namespace}.svc.cluster.local`,
      port: NATS_CLIENT_PORT,
    },
  };
}

/**
 * DELETE-verb counterpart to provisionProjectQueue -- same idempotent
 * not-found handling lib/redis.ts's teardownProjectRedis already
 * establishes (a 404 from the API server is treated as already-torn-down,
 * not an error). Deletes the NetworkPolicy/Deployment/Service first, the
 * Secret last, so a mid-teardown failure never leaves the password
 * Secret deleted while the Deployment referencing it still exists.
 */
export async function teardownProjectQueue(project: SupabaseProject): Promise<K8sResult<null>> {
  const name = queueResourceName(project.name);
  const namespace = project.namespace;

  const netpolResult = await k8sRequest(
    `/apis/networking.k8s.io/v1/namespaces/${encodeURIComponent(namespace)}/networkpolicies/${encodeURIComponent(`${name}-netpol`)}`,
    "DELETE",
  );
  if (!netpolResult.ok && !/not found/i.test(netpolResult.error)) return netpolResult;

  const deploymentResult = await k8sRequest(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!deploymentResult.ok && !/not found/i.test(deploymentResult.error)) return deploymentResult;

  const serviceResult = await k8sRequest(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/services/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!serviceResult.ok && !/not found/i.test(serviceResult.error)) return serviceResult;

  const secretResult = await deleteSecret(namespace, name);
  if (!secretResult.ok && !/not found/i.test((secretResult as { error: string }).error ?? "")) {
    return secretResult;
  }

  return { ok: true, data: null };
}
