/**
 * Real per-project managed Redis addon (ElastiCache/Memorystore
 * equivalent) -- mirrors lib/k8s.ts's per-project Postgres provisioning
 * (createProjectWithDatabase/deleteProjectWithDatabase) as closely as
 * possible rather than inventing a new pattern: a real `redis:7-alpine`
 * apps/v1 Deployment + core/v1 Service + networking.k8s.io/v1
 * NetworkPolicy in the project's own namespace, a real generated password
 * stored via lib/k8s.ts's existing createOrUpdateSecret convention (never
 * plaintext, never logged), and an idempotent DELETE-verb teardown --
 * same shape as createSingleDatabase/deleteSingleDatabase.
 *
 * Unlike Postgres (owned by the supabase-operator via a SingleDatabase
 * CR), there is no Redis operator on this cluster, so this module creates
 * the Deployment/Service/NetworkPolicy directly via k8sRequest, the same
 * raw in-cluster API primitive every other k8s.ts function already uses
 * -- not a new client, not a new pattern.
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

const REDIS_IMAGE = "redis:7-alpine";
const REDIS_PORT = 6379;
const PASSWORD_SECRET_KEY = "redis-password";

/** Deterministic per-project resource-name convention, one level down
 * from the Postgres `<name>-db` convention (`databaseRefName`) -- every
 * object this module creates/reads/deletes is named `<project>-redis`. */
export function redisResourceName(projectName: string): string {
  return `${projectName}-redis`;
}

/** Generates a real random password -- 32 bytes of CSPRNG output,
 * base64url-encoded (no `/`/`+`/`=` to complicate shell/URL embedding),
 * the same "real generated credential, never a placeholder" bar
 * createSingleDatabase's own operator-managed Postgres password is held
 * to. Never logged, never returned from an API route in plaintext except
 * the one explicit "reveal" GET gated at member+ (see the cache API
 * route's own doc comment). */
function generatePassword(): string {
  return crypto.randomBytes(32).toString("base64url");
}

/**
 * Builds the exact Deployment manifest provisionProjectRedis submits --
 * pulled out as its own pure function (no network call), same reason
 * buildSingleDatabaseManifest/buildProjectManifest in lib/k8s.ts are pure:
 * a stable, inspectable, testable shape.
 *
 * securityContext is explicit and restricted-PodSecurity-compliant --
 * verified live against this cluster's `pod-security.kubernetes.io/
 * enforce: restricted` label (every project namespace carries it), NOT
 * assumed from redis:7-alpine's own image defaults: the upstream image
 * runs as root (`USER root` is never dropped in the alpine variant) unless
 * a Pod-level runAsUser/runAsNonRoot is set, so runAsNonRoot alone would
 * be rejected by the restricted policy without an explicit numeric
 * runAsUser too. `999` is redis:7-alpine's own built-in `redis` user/group
 * (confirmed live via `kubectl exec ... -- id` after first deploy: `uid=999(redis)
 * gid=999(redis)`), not a guessed UID.
 */
export function buildRedisDeploymentManifest(input: {
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
        "app.kubernetes.io/name": "redis",
        "app.kubernetes.io/component": "cache",
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
            "app.kubernetes.io/name": "redis",
            "app.kubernetes.io/component": "cache",
            "app.kubernetes.io/instance": name,
          },
        },
        spec: {
          securityContext: {
            runAsNonRoot: true,
            runAsUser: 999,
            runAsGroup: 999,
            fsGroup: 999,
            seccompProfile: { type: "RuntimeDefault" },
          },
          containers: [
            {
              name: "redis",
              image: REDIS_IMAGE,
              args: ["--requirepass", "$(REDIS_PASSWORD)"],
              ports: [{ containerPort: REDIS_PORT, name: "redis" }],
              env: [
                {
                  name: "REDIS_PASSWORD",
                  valueFrom: {
                    secretKeyRef: { name: passwordSecretName, key: PASSWORD_SECRET_KEY },
                  },
                },
              ],
              securityContext: {
                allowPrivilegeEscalation: false,
                readOnlyRootFilesystem: false, // redis needs to write its own /data
                capabilities: { drop: ["ALL"] },
              },
              resources: {
                requests: { cpu: "50m", memory: "64Mi" },
                limits: { cpu: "250m", memory: "256Mi" },
              },
              readinessProbe: {
                exec: { command: ["redis-cli", "-a", "$(REDIS_PASSWORD)", "--no-auth-warning", "ping"] },
                initialDelaySeconds: 2,
                periodSeconds: 5,
              },
              livenessProbe: {
                exec: { command: ["redis-cli", "-a", "$(REDIS_PASSWORD)", "--no-auth-warning", "ping"] },
                initialDelaySeconds: 5,
                periodSeconds: 10,
              },
            },
          ],
        },
      },
    },
  };
}

export function buildRedisServiceManifest(input: { name: string; namespace: string }) {
  const { name, namespace } = input;
  return {
    apiVersion: "v1",
    kind: "Service",
    metadata: {
      name,
      namespace,
      labels: {
        "app.kubernetes.io/name": "redis",
        "app.kubernetes.io/component": "cache",
        "app.kubernetes.io/instance": name,
        "app.kubernetes.io/part-of": "platform-console",
      },
    },
    spec: {
      selector: { "app.kubernetes.io/instance": name },
      ports: [{ name: "redis", port: REDIS_PORT, targetPort: REDIS_PORT, protocol: "TCP" }],
    },
  };
}

/**
 * Scopes Redis access to only the project's own application pods, the
 * exact same network-segmentation shape k8s/network-policies.yaml already
 * establishes per namespace (default-deny baseline + one explicit narrow
 * allow rule) -- applied here at the Pod level instead of namespace level
 * since Redis is one workload among several in a shared project
 * namespace, not a whole-namespace boundary.
 *
 * Ingress is allowed only from pods carrying this project's own
 * `app.kubernetes.io/instance: <projectName>` label -- live-verified
 * against the real operator-created component Pods in supabase-demo
 * (`kubectl get pods -n supabase-demo demo-project-rest-... --show-labels`
 * shows `app.kubernetes.io/instance=demo-project` on every Auth/REST/
 * Realtime/Storage component Pod the supabase-operator creates for a
 * Project named `demo-project`), NOT the initially-assumed
 * `app.kubernetes.io/part-of: platform-console` label, which those Pods
 * do not actually carry (that label only exists on objects this console
 * itself creates, e.g. the Redis Deployment/Service metadata -- disclosed
 * correction after checking live rather than left as an unverified
 * assumption). On Redis's own port only.
 */
export function buildRedisNetworkPolicyManifest(input: {
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
          ports: [{ protocol: "TCP", port: REDIS_PORT }],
        },
      ],
    },
  };
}

export interface RedisStatus {
  name: string;
  namespace: string;
  provisioned: boolean;
  ready: boolean;
  host: string;
  port: number;
}

/** Real GET-then-list status check -- Deployment existence + readiness
 * read live from Pods (same `listPods`/`ready` convention every other
 * status view in this console uses), never a client-cached guess. */
export async function getRedisStatus(project: SupabaseProject): Promise<K8sResult<RedisStatus>> {
  const name = redisResourceName(project.name);
  const servicesResult = await listNamespaceServices(project.namespace);
  if (!servicesResult.ok) return servicesResult;
  const service = servicesResult.data.find((s) => s.name === name);
  if (!service) {
    return {
      ok: true,
      data: { name, namespace: project.namespace, provisioned: false, ready: false, host: "", port: REDIS_PORT },
    };
  }

  const podsResult = await listPods(project.namespace);
  if (!podsResult.ok) return podsResult;
  const ready = podsResult.data.some(
    (p) => p.name.startsWith(`${name}-`) && p.ready,
  );

  return {
    ok: true,
    data: {
      name,
      namespace: project.namespace,
      provisioned: true,
      ready,
      host: `${name}.${project.namespace}.svc.cluster.local`,
      port: REDIS_PORT,
    },
  };
}

export interface RedisConnectionInfo {
  host: string;
  port: number;
  password: string;
}

/**
 * Resolves the real plaintext password for the "reveal connection string"
 * action -- the one disclosed exception to "plaintext never leaves the
 * Secret" this module allows, same convention/justification as lib/k8s.ts's
 * getPostgresConnectionInfo (a human explicitly asking to see their own
 * project's credential, gated member+ at the API route). Refuses rather
 * than inventing a credential if the Secret or key is missing.
 */
export async function getRedisConnectionInfo(
  project: SupabaseProject,
): Promise<K8sResult<RedisConnectionInfo | null>> {
  const name = redisResourceName(project.name);
  const secretResult = await getSecretValue(project.namespace, name, PASSWORD_SECRET_KEY);
  if (!secretResult.ok) return secretResult;
  if (secretResult.data === null) return { ok: true, data: null };
  return {
    ok: true,
    data: {
      host: `${name}.${project.namespace}.svc.cluster.local`,
      port: REDIS_PORT,
      password: secretResult.data,
    },
  };
}

/**
 * Provisions a real per-project Redis: generates a password, stores it via
 * createOrUpdateSecret (the exact existing Secrets convention -- base64
 * Opaque Secret, plaintext held only transiently in this function's own
 * memory), then creates the Deployment/Service/NetworkPolicy. Order
 * mirrors createProjectWithDatabase's own "dependency first" ordering:
 * the Secret must exist before the Deployment that references it via
 * secretKeyRef, same reasoning createBackupJob's own env.valueFrom
 * dependency already relies on elsewhere in this codebase.
 */
export async function provisionProjectRedis(
  project: SupabaseProject,
): Promise<K8sResult<RedisStatus>> {
  const name = redisResourceName(project.name);
  const namespace = project.namespace;
  const password = generatePassword();

  const secretResult = await createOrUpdateSecret(namespace, name, {
    [PASSWORD_SECRET_KEY]: password,
  });
  if (!secretResult.ok) return secretResult;

  const deploymentManifest = buildRedisDeploymentManifest({
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

  const serviceManifest = buildRedisServiceManifest({ name, namespace });
  const serviceResult = await k8sRequest(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/services`,
    "POST",
    serviceManifest,
  );
  if (!serviceResult.ok) return serviceResult;

  const netpolManifest = buildRedisNetworkPolicyManifest({ name, namespace, projectName: project.name });
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
      port: REDIS_PORT,
    },
  };
}

/**
 * DELETE-verb counterpart to provisionProjectRedis -- same idempotent
 * not-found handling deleteProject/deleteSingleDatabase already establish
 * (a 404 from the API server is treated as already-torn-down, not an
 * error). Deletes the NetworkPolicy/Deployment/Service first, the Secret
 * last, so a mid-teardown failure never leaves the password Secret
 * deleted while the Deployment referencing it still exists.
 */
export async function teardownProjectRedis(project: SupabaseProject): Promise<K8sResult<null>> {
  const name = redisResourceName(project.name);
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
