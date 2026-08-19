// -------------------------------------------------------- Scheduled Jobs
//
// Real hyperscaler-PaaS-style Scheduled Jobs primitive (AWS EventBridge
// Scheduler / GCP Cloud Scheduler / Azure Logic Apps recurring-trigger
// equivalent): self-service creation of real k8s `batch/v1` CronJobs,
// scoped by k8s/paas-rbac.yaml to a Role+RoleBinding per platform
// namespace -- the exact same per-namespace pattern the Secrets Manager
// and Database Backups modules already use (never cluster-wide), for the
// same reason: a CronJob's Pod runs a real container on a real schedule,
// unattended, so this is a genuine multi-tenant blast-radius boundary,
// not a formality.
//
// The COMMAND a CronJob runs is never taken verbatim from user input. A
// user-supplied command string reaching `command: ["sh", "-c", <string>]`
// would be a real, textbook shell-injection primitive -- the exact
// opposite of "self-service" done safely. Instead, `ALLOWED_COMMANDS`
// below is a fixed, small, server-side allowlist of real, harmless
// command *ids*; the caller picks an id, never raw text, and this module
// resolves that id to the one, fixed, hardcoded command array it maps to.
// `resolveCommand` is the one and only place a request's `commandId`
// touches anything that becomes a container `command` -- it validates
// against the allowlist and returns `null` on anything else, so a
// request naming an unknown id is rejected before any k8s API call is
// ever made. This allowlist is the real security boundary this module
// promises, not a decorative comment: there is no code path anywhere in
// this file that accepts free-form shell text.
import { k8sRequest, type K8sResult } from "@/lib/k8s";

export interface AllowedCommand {
  id: AllowedCommandId;
  label: string;
  description: string;
  image: string;
}

/** The fixed, closed set of command ids -- declared as its own literal
 * union (not derived via `keyof typeof ALLOWED_COMMANDS`) so
 * `buildContainerCommand`'s switch below is statically checked exhaustive
 * by the compiler: adding a new id to this union without adding a case
 * there is a real compile error, not a silent `undefined` command. */
export type AllowedCommandId = "echo-timestamp" | "curl-status" | "cost-report-snapshot";

/**
 * The fixed, small allowlist. Every entry maps to one hardcoded container
 * command (built by `buildContainerCommand` below, using only the
 * namespace -- itself always one of `SCHEDULABLE_NAMESPACES`, never raw
 * user text) -- never user-supplied shell text. Add a new command here by
 * adding a new fixed id + hardcoded behavior, never by templating
 * arbitrary input into a shell string.
 */
export const ALLOWED_COMMANDS: Record<AllowedCommandId, AllowedCommand> = {
  "echo-timestamp": {
    id: "echo-timestamp",
    label: "Echo a timestamp",
    description:
      "Prints the real current UTC timestamp to the Job's own pod log -- the smallest possible real, harmless action a schedule can trigger.",
    image: "busybox:1.36",
  },
  "curl-status": {
    id: "curl-status",
    label: "Curl the namespace's status service",
    description:
      "curl's this namespace's own <namespace>-status Service at /status (cluster-internal only, 10s timeout) and logs the real HTTP response to the Job's own pod log.",
    image: "curlimages/curl:8.10.1",
  },
  "cost-report-snapshot": {
    id: "cost-report-snapshot",
    label: "Capture a cost & usage report snapshot",
    description:
      "POSTs this console's own internal /api/internal/cost-report-snapshot route (cluster-internal only, shared-secret authenticated), which re-runs the same real, metered-from-Prometheus usage computation lib/invoice-preview.ts already exposes on demand for this CronJob's own namespace and appends one record to that namespace's cost-report history -- the FinOps-trend capability this command exists to schedule.",
    image: "curlimages/curl:8.10.1",
  },
};

function isAllowedCommandId(value: string): value is AllowedCommandId {
  return Object.prototype.hasOwnProperty.call(ALLOWED_COMMANDS, value as AllowedCommandId);
}

/**
 * Resolves a caller-supplied string against the allowlist. Returns the
 * real `AllowedCommand` record on a match, `null` on anything else --
 * callers (the API route) must treat `null` as "reject the request",
 * never fall back to a default command.
 */
export function resolveCommand(commandId: string): AllowedCommand | null {
  return isAllowedCommandId(commandId) ? ALLOWED_COMMANDS[commandId] : null;
}

/**
 * Builds the real, fixed container `command` array for one allowlisted
 * command id. `namespace` is the only substitution ever performed, and it
 * is always one of `SCHEDULABLE_NAMESPACES` (validated by the API route
 * before this is ever called) -- never raw request text -- so this never
 * becomes a second injection surface. No other field of the request
 * (name, schedule) is ever interpolated into a command string.
 */
function buildContainerCommand(commandId: AllowedCommandId, namespace: string): string[] {
  switch (commandId) {
    case "echo-timestamp":
      return ["sh", "-c", "date -u +'scheduled-job ran at %Y-%m-%dT%H:%M:%SZ'"];
    case "curl-status":
      return [
        "sh",
        "-c",
        `curl -sS -m 10 "http://${namespace}-status.${namespace}.svc.cluster.local/status" && echo`,
      ];
    case "cost-report-snapshot":
      // Same cluster-internal, shared-secret-authenticated curl shape as
      // buildComplianceReportCommand/buildRetentionPurgeCronCommand below
      // -- POSTs this console's own Service DNS name, never a raw user
      // command. `namespace` (this CronJob's own namespace, always one of
      // SCHEDULABLE_NAMESPACES) travels as a request header, the same way
      // buildComplianceReportCommand threads `orgId` into its target
      // path -- the internal route (never this module) is the one place
      // that header is validated before being used as a k8s namespace.
      return [
        "sh",
        "-c",
        `curl -sS -m 30 -X POST -H "x-cost-report-cron-secret: $COST_REPORT_CRON_SECRET" ` +
          `-H "x-cost-report-namespace: ${namespace}" ` +
          `"http://platform-console.platform-console.svc.cluster.local/api/internal/cost-report-snapshot" && echo`,
      ];
  }
}

/**
 * The platform's own namespaces only -- identical to the Secrets Manager
 * module's `PLATFORM_NAMESPACES` (`app/secrets/page.tsx`) and to the
 * Role+RoleBinding pairs granted in k8s/paas-rbac.yaml's Scheduled Jobs
 * section below. Never cluster-wide, never kube-system: this list IS the
 * RBAC scope, both here and in the manifest that backs it.
 */
export const SCHEDULABLE_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
] as const;

export type SchedulableNamespace = (typeof SCHEDULABLE_NAMESPACES)[number];

export function isSchedulableNamespace(value: string): value is SchedulableNamespace {
  return (SCHEDULABLE_NAMESPACES as readonly string[]).includes(value);
}

// A real 5-field cron expression (minute hour day-of-month month
// day-of-week), the same field shape AWS EventBridge Scheduler's
// `cron(...)`/`rate(...)` and GCP Cloud Scheduler's `unix-cron` both
// accept for a recurring trigger. Not a security boundary (a schedule
// string is data the CronJob controller parses, never executed as
// shell) -- this is a real syntax check so a malformed schedule fails
// fast with a clear message instead of a cryptic k8s admission error,
// same reasoning CreateSecretForm's `pattern` attribute uses for names.
const CRON_FIELD = "(\\*|[0-9,\\-/*]+)";
const CRON_SCHEDULE_RE = new RegExp(`^${CRON_FIELD}( ${CRON_FIELD}){4}$`);

export function isValidCronSchedule(schedule: string): boolean {
  return CRON_SCHEDULE_RE.test(schedule.trim());
}

// RFC 1123 DNS label -- same pattern CreateSecretForm's `name` input uses.
const NAME_RE = /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/;

export function isValidJobName(name: string): boolean {
  return name.length > 0 && name.length <= 52 && NAME_RE.test(name);
}

export interface ScheduledJob {
  name: string;
  namespace: string;
  schedule: string;
  suspend: boolean;
  commandId: string | null; // null when a CronJob wasn't created by this module (unrecognized label)
  image: string | null;
  createdAt: string;
  lastScheduleTime: string | null;
  lastSuccessfulTime: string | null;
}

interface CronJobItem {
  metadata: {
    name: string;
    namespace: string;
    creationTimestamp: string;
    labels?: Record<string, string>;
  };
  spec?: {
    schedule?: string;
    suspend?: boolean;
    jobTemplate?: {
      spec?: { template?: { spec?: { containers?: Array<{ image?: string }> } } };
    };
  };
  status?: {
    lastScheduleTime?: string;
    lastSuccessfulTime?: string;
  };
}

interface CronJobListResponse {
  items?: CronJobItem[];
}

const MANAGED_BY_LABEL = "app";
const MANAGED_BY_VALUE = "platform-scheduled-jobs";
const COMMAND_LABEL = "scheduled-job-command";

function toScheduledJob(item: CronJobItem): ScheduledJob {
  const commandId = item.metadata.labels?.[COMMAND_LABEL] ?? null;
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    schedule: item.spec?.schedule ?? "",
    suspend: item.spec?.suspend ?? false,
    commandId,
    image: item.spec?.jobTemplate?.spec?.template?.spec?.containers?.[0]?.image ?? null,
    createdAt: item.metadata.creationTimestamp,
    lastScheduleTime: item.status?.lastScheduleTime ?? null,
    lastSuccessfulTime: item.status?.lastSuccessfulTime ?? null,
  };
}

/**
 * Lists real `batch/v1` CronJobs in one namespace, filtered to the ones
 * this module itself created (`app=platform-scheduled-jobs`) so a
 * cluster-internal CronJob some other tool creates in the same namespace
 * (there are none today, but the filter costs nothing and matches the
 * same "never show objects this module didn't create" convention the
 * Backups module's `listJobs(namespace, "app=platform-backups")` already
 * uses). `extraLabelSelector`, when given, is AND-ed onto the same real
 * `?labelSelector=` query parameter (comma-separated selectors are a real
 * k8s API AND, not a client-side second pass) -- used by lib/tags.ts's
 * listResourcesByTag to add a real
 * `platform-console.io/tag-<key>=<value>` clause for a genuine
 * server-side "browse by tag" filter.
 */
export async function listCronJobs(
  namespace: string,
  extraLabelSelector?: string,
): Promise<K8sResult<ScheduledJob[]>> {
  const selector = extraLabelSelector
    ? `${MANAGED_BY_LABEL}=${MANAGED_BY_VALUE},${extraLabelSelector}`
    : `${MANAGED_BY_LABEL}=${MANAGED_BY_VALUE}`;
  const result = await k8sRequest<CronJobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/cronjobs?labelSelector=${encodeURIComponent(selector)}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toScheduledJob) };
}

// Real shared-secret env var the "cost-report-snapshot" command's curl
// call authenticates with -- same one-time-operator-provisioning
// convention as COMPLIANCE_CRON_SECRET_NAME below (`kubectl create secret
// generic platform-cost-report-cron-secret --from-literal=secret=...` in
// the `platform-console` namespace, then setting a matching
// `COST_REPORT_CRON_SECRET` env on the console's own Deployment so
// POST /api/internal/cost-report-snapshot can compare against it). Only
// this one command id's CronJob Pod gets this env injected (see
// createCronJob below) -- every other ALLOWED_COMMANDS entry is
// unaffected.
export const COST_REPORT_CRON_SECRET_NAME = "platform-cost-report-cron-secret";
export const COST_REPORT_CRON_SECRET_KEY = "secret";

export interface CreateCronJobInput {
  namespace: SchedulableNamespace;
  name: string;
  schedule: string;
  commandId: AllowedCommandId;
}

/**
 * Creates a real `batch/v1` CronJob. Every field that ends up inside the
 * Job's own container `command` traces back to `buildContainerCommand`
 * above -- `commandId` is already a validated `AllowedCommandId` by the
 * time this function is called (see `resolveCommand`), never raw text.
 * `concurrencyPolicy: Forbid` + `backoffLimit: 0` keep each firing to at
 * most one real Job Pod, never an overlapping pile-up. History limits are
 * small (3/3) so `kubectl get jobs` and this module's own inventory stay
 * a short, real, honest list rather than growing unbounded.
 */
export async function createCronJob(
  input: CreateCronJobInput,
): Promise<K8sResult<ScheduledJob>> {
  const command = ALLOWED_COMMANDS[input.commandId];
  const manifest = {
    apiVersion: "batch/v1",
    kind: "CronJob",
    metadata: {
      name: input.name,
      namespace: input.namespace,
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: input.commandId,
      },
    },
    spec: {
      schedule: input.schedule,
      concurrencyPolicy: "Forbid",
      successfulJobsHistoryLimit: 3,
      failedJobsHistoryLimit: 3,
      jobTemplate: {
        spec: {
          backoffLimit: 0,
          activeDeadlineSeconds: 60,
          template: {
            metadata: {
              labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "cronjob-name": input.name },
            },
            spec: {
              restartPolicy: "Never",
              containers: [
                {
                  name: "scheduled-job",
                  image: command.image,
                  imagePullPolicy: "IfNotPresent",
                  command: buildContainerCommand(input.commandId, input.namespace),
                  // Only the "cost-report-snapshot" command's curl call
                  // needs to authenticate itself against this console's
                  // own internal route -- every other ALLOWED_COMMANDS
                  // entry curls either nothing external
                  // (echo-timestamp) or an unauthenticated in-namespace
                  // status Service (curl-status), so this stays absent
                  // (undefined, meaning "no env" per this manifest's own
                  // JSON.stringify -> k8s POST path) for those.
                  ...(input.commandId === "cost-report-snapshot"
                    ? {
                        env: [
                          {
                            name: "COST_REPORT_CRON_SECRET",
                            valueFrom: {
                              secretKeyRef: {
                                name: COST_REPORT_CRON_SECRET_NAME,
                                key: COST_REPORT_CRON_SECRET_KEY,
                              },
                            },
                          },
                        ],
                      }
                    : {}),
                  // Real, live-discovered requirement, not a stylistic
                  // choice: 4 of this platform's 5 schedulable namespaces
                  // carry a ResourceQuota with hard `limits.cpu`/
                  // `limits.memory` (k8s/resource-quotas.yaml) -- any
                  // ResourceQuota setting those keys forces the API
                  // server's own admission controller to reject every
                  // new Pod that doesn't declare matching
                  // requests/limits, confirmed live the first time this
                  // module's CronJob fired without them (`forbidden:
                  // failed quota: ...-quota: must specify limits.cpu for:
                  // scheduled-job; ...`). Sized deliberately small --
                  // these are single-shot `echo`/`curl` commands, not a
                  // real workload -- well under every project namespace's
                  // quota headroom.
                  resources: {
                    requests: { cpu: "10m", memory: "16Mi" },
                    limits: { cpu: "50m", memory: "32Mi" },
                  },
                },
              ],
            },
          },
        },
      },
    },
  };

  const result = await k8sRequest<CronJobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(input.namespace)}/cronjobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toScheduledJob(result.data) };
}

// ---------------------------------------------------- Compliance Reports
//
// Real per-org recurring compliance-report CronJob (lib/compliance-
// report.ts's own capability): unlike the `ALLOWED_COMMANDS` CronJobs
// above -- deliberately restricted to `SCHEDULABLE_NAMESPACES`, this
// platform's own 5 fixed operational namespaces -- a compliance report is
// scheduled inside a CUSTOMER ORG's own namespace (lib/orgs.ts's
// dynamically-provisioned `org-<slug>-<suffix>`, or this deployment's one
// single-tenant `platform-console` namespace fallback -- see
// lib/orgs.ts's `getOrg` and every `/api/orgs/[id]/*` route's identical
// "id resolves via the registry, or id IS the namespace" convention),
// which is why this is its own function rather than a 6th
// `SCHEDULABLE_NAMESPACES` entry: an org namespace is not a fixed,
// enumerable list.
//
// Same "no free-form shell text reaches a container command" invariant
// as `buildContainerCommand` above: the only two values interpolated
// into the fixed curl template are `namespace` and `orgId`, both already
// validated identifiers by the time this is called (a real k8s namespace
// name / a real registry id or namespace string), never raw request
// text. The internal secret the curl call authenticates with
// (`COMPLIANCE_CRON_SECRET`, checked by
// POST /api/orgs/[id]/compliance-reports against its own
// `process.env.COMPLIANCE_CRON_SECRET`) is injected via a real k8s
// `secretKeyRef` against a `platform-compliance-cron-secret` Secret this
// module never creates itself -- provisioning that Secret (`kubectl
// create secret generic platform-compliance-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting the matching `COMPLIANCE_CRON_SECRET` env on the console's own
// Deployment) is a one-time operator/manifest step, same "documented, not
// silently claimed done" disclosure this file's header already uses for
// the RBAC grants a new schedulable namespace needs. On-demand generation
// (an owner clicking "Generate now" in app/org/compliance/page.tsx) does
// NOT need this secret at all -- it authenticates with the owner's own
// session/API key, the same as every other mutating route in this app.
export const COMPLIANCE_CRON_SECRET_NAME = "platform-compliance-cron-secret";
export const COMPLIANCE_CRON_SECRET_KEY = "secret";
export const COMPLIANCE_CRON_JOB_LABEL = "compliance-report-cronjob";

/**
 * The real, fixed curl command a compliance-report CronJob's Pod runs --
 * cluster-internal only (same trust boundary `curl-status` above already
 * documents), POSTing to this console's own in-cluster Service DNS name
 * (`platform-console.platform-console.svc.cluster.local`, the same
 * `<name>.<namespace>.svc.cluster.local` convention `buildContainerCommand`
 * already uses for `curl-status`'s target). `orgId` and `namespace` are
 * both plain path/URL-safe strings (a UUID or a k8s namespace name) by the
 * time this is called; neither is ever raw, un-validated request text.
 */
function buildComplianceReportCommand(orgId: string): string[] {
  return [
    "sh",
    "-c",
    `curl -sS -m 30 -X POST -H "x-compliance-cron-secret: $COMPLIANCE_CRON_SECRET" ` +
      `"http://platform-console.platform-console.svc.cluster.local/api/orgs/${orgId}/compliance-reports" && echo`,
  ];
}

/**
 * Creates the real, per-org recurring compliance-report CronJob. `name`
 * must already pass `isValidJobName` and `schedule` must already pass
 * `isValidCronSchedule` -- same caller-validates-before-calling contract
 * `createCronJob` above uses; this function does not itself re-validate,
 * consistent with the rest of this module.
 */
export async function createComplianceReportCronJob(input: {
  namespace: string;
  orgId: string;
  name: string;
  schedule: string;
}): Promise<K8sResult<ScheduledJob>> {
  const manifest = {
    apiVersion: "batch/v1",
    kind: "CronJob",
    metadata: {
      name: input.name,
      namespace: input.namespace,
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: COMPLIANCE_CRON_JOB_LABEL,
      },
    },
    spec: {
      schedule: input.schedule,
      concurrencyPolicy: "Forbid",
      successfulJobsHistoryLimit: 3,
      failedJobsHistoryLimit: 3,
      jobTemplate: {
        spec: {
          backoffLimit: 0,
          activeDeadlineSeconds: 60,
          template: {
            metadata: {
              labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "cronjob-name": input.name },
            },
            spec: {
              restartPolicy: "Never",
              containers: [
                {
                  name: "compliance-report",
                  image: "curlimages/curl:8.10.1",
                  imagePullPolicy: "IfNotPresent",
                  command: buildComplianceReportCommand(input.orgId),
                  env: [
                    {
                      name: "COMPLIANCE_CRON_SECRET",
                      valueFrom: {
                        secretKeyRef: {
                          name: COMPLIANCE_CRON_SECRET_NAME,
                          key: COMPLIANCE_CRON_SECRET_KEY,
                        },
                      },
                    },
                  ],
                  resources: {
                    requests: { cpu: "10m", memory: "16Mi" },
                    limits: { cpu: "50m", memory: "32Mi" },
                  },
                },
              ],
            },
          },
        },
      },
    },
  };

  const result = await k8sRequest<CronJobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(input.namespace)}/cronjobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toScheduledJob(result.data) };
}

// -------------------------------------------------- Export Subscriptions
//
// Real recurring "bring your own bucket" export delivery
// (lib/s3-export-subscription.ts): unlike createComplianceReportCronJob
// above (one CronJob per org, each POSTing into ITS OWN org id path),
// this one platform-wide CronJob fans out across every org in a single
// firing -- lib/s3-export-subscription.ts's runDueExportSubscriptions
// already walks the whole `platform-console-export-subscriptions`
// registry and skips anything not yet due (isSubscriptionDue), so there
// is no need for a per-org schedule/CronJob object at all; one CronJob in
// the platform's own `platform-console` namespace, firing more often than
// the shortest configured cadence (daily), is both simpler and avoids
// creating/tearing down a CronJob every time an org enables or disables
// its subscription.
//
// Same shared-secret authentication pattern as
// COMPLIANCE_CRON_SECRET/buildComplianceReportCommand above (see that
// header comment for the one-time operator provisioning step): the
// secret is injected via a real k8s `secretKeyRef` against a
// `platform-export-subscription-cron-secret` Secret this module never
// creates itself, and the only two values ever interpolated into the
// fixed curl template are constants -- never request-supplied text.
export const EXPORT_SUBSCRIPTION_CRON_SECRET_NAME = "platform-export-subscription-cron-secret";
export const EXPORT_SUBSCRIPTION_CRON_SECRET_KEY = "secret";
export const EXPORT_SUBSCRIPTION_CRON_JOB_NAME = "platform-export-subscriptions";
export const EXPORT_SUBSCRIPTION_CRON_JOB_LABEL = "export-subscription-cronjob";
// Fires every 4 hours -- comfortably more often than the shortest
// configured cadence ("daily", due after 20h per isSubscriptionDue), so
// no enabled subscription can ever drift more than one firing interval
// past its own due window.
export const EXPORT_SUBSCRIPTION_CRON_SCHEDULE = "23 */4 * * *";

function buildExportSubscriptionCronCommand(): string[] {
  return [
    "sh",
    "-c",
    `curl -sS -m 60 -X POST -H "x-export-subscription-cron-secret: $EXPORT_SUBSCRIPTION_CRON_SECRET" ` +
      `"http://platform-console.platform-console.svc.cluster.local/api/orgs/_cron/export-subscription" && echo`,
  ];
}

/**
 * Creates the real, one-per-deployment recurring export-subscription
 * CronJob in the `platform-console` namespace. Idempotent from the
 * caller's perspective the same way createComplianceReportCronJob's own
 * callers are expected to be -- calling this twice creates two CronJobs
 * with the same fixed name only if the k8s API itself allows it (it does
 * not; a second POST for the same name 409s, surfaced as a real
 * `K8sResult` error, not silently swallowed).
 */
export async function createExportSubscriptionCronJob(): Promise<K8sResult<ScheduledJob>> {
  const manifest = {
    apiVersion: "batch/v1",
    kind: "CronJob",
    metadata: {
      name: EXPORT_SUBSCRIPTION_CRON_JOB_NAME,
      namespace: "platform-console",
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: EXPORT_SUBSCRIPTION_CRON_JOB_LABEL,
      },
    },
    spec: {
      schedule: EXPORT_SUBSCRIPTION_CRON_SCHEDULE,
      concurrencyPolicy: "Forbid",
      successfulJobsHistoryLimit: 3,
      failedJobsHistoryLimit: 3,
      jobTemplate: {
        spec: {
          backoffLimit: 0,
          activeDeadlineSeconds: 120,
          template: {
            metadata: {
              labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "cronjob-name": EXPORT_SUBSCRIPTION_CRON_JOB_NAME },
            },
            spec: {
              restartPolicy: "Never",
              containers: [
                {
                  name: "export-subscriptions",
                  image: "curlimages/curl:8.10.1",
                  imagePullPolicy: "IfNotPresent",
                  command: buildExportSubscriptionCronCommand(),
                  env: [
                    {
                      name: "EXPORT_SUBSCRIPTION_CRON_SECRET",
                      valueFrom: {
                        secretKeyRef: {
                          name: EXPORT_SUBSCRIPTION_CRON_SECRET_NAME,
                          key: EXPORT_SUBSCRIPTION_CRON_SECRET_KEY,
                        },
                      },
                    },
                  ],
                  resources: {
                    requests: { cpu: "10m", memory: "16Mi" },
                    limits: { cpu: "50m", memory: "32Mi" },
                  },
                },
              ],
            },
          },
        },
      },
    },
  };

  const result = await k8sRequest<CronJobItem>(
    `/apis/batch/v1/namespaces/platform-console/cronjobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toScheduledJob(result.data) };
}

// ------------------------------------------------------ Backup Retention
//
// Real per-org recurring backup CronJob (lib/backup-retention.ts's own
// capability): same "org namespace is not a fixed, enumerable list" split
// from `createCronJob` above that `createComplianceReportCronJob`
// already established -- this is its own function, not a 6th
// `SCHEDULABLE_NAMESPACES` entry.
//
// Unlike the compliance CronJob (which authenticates with a dedicated
// `COMPLIANCE_CRON_SECRET` header this console's own route checks),
// this CronJob authenticates the SAME way any of this console's own API
// automation would: a real `Authorization: Bearer <api key>` header
// against the live `platform-console-api-keys` Secret
// (lib/api-keys.ts/middleware.ts's existing Bearer-API-key auth path) --
// no new auth mechanism, no new route-level secret check. The API key
// itself is injected via a real k8s `secretKeyRef` against a
// `platform-backup-cron-secret` Secret this module never creates itself
// (provisioning it -- `kubectl create secret generic
// platform-backup-cron-secret --from-literal=apiKey=pk_live_...` in the
// `platform-console` namespace, using a real key minted through this
// org's own API-keys UI -- is a one-time operator step, same
// documented-not-silently-claimed-done disclosure
// `createComplianceReportCronJob`'s header comment already uses for a
// new schedulable namespace's RBAC grants).
//
// Hits GET /api/orgs/<orgId>/backups, which itself runs
// cleanupExpiredBackups (real Job delete + ConfigMap row removal) before
// returning -- so this CronJob's real, scheduled side effect IS the
// tiered retention enforcement the capability's spec asks for, using the
// exact same code path a human viewing the backup-history page triggers,
// never a separate/duplicated cleanup implementation.
export const BACKUP_CRON_SECRET_NAME = "platform-backup-cron-secret";
export const BACKUP_CRON_SECRET_KEY = "apiKey";
export const BACKUP_CRON_JOB_LABEL = "backup-retention-cronjob";

function buildBackupRetentionCommand(orgId: string): string[] {
  return [
    "sh",
    "-c",
    `curl -sS -m 30 -H "Authorization: Bearer $BACKUP_CRON_API_KEY" ` +
      `"http://platform-console.platform-console.svc.cluster.local/api/orgs/${orgId}/backups" && echo`,
  ];
}

/**
 * Creates the real, per-org recurring backup-retention-enforcement
 * CronJob. `name` must already pass `isValidJobName` and `schedule` must
 * already pass `isValidCronSchedule` -- same caller-validates-before-
 * calling contract `createCronJob`/`createComplianceReportCronJob` above
 * use.
 */
export async function createOrgBackupCronJob(input: {
  namespace: string;
  orgId: string;
  name: string;
  schedule: string;
}): Promise<K8sResult<ScheduledJob>> {
  const manifest = {
    apiVersion: "batch/v1",
    kind: "CronJob",
    metadata: {
      name: input.name,
      namespace: input.namespace,
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: BACKUP_CRON_JOB_LABEL,
      },
    },
    spec: {
      schedule: input.schedule,
      concurrencyPolicy: "Forbid",
      successfulJobsHistoryLimit: 3,
      failedJobsHistoryLimit: 3,
      jobTemplate: {
        spec: {
          backoffLimit: 0,
          activeDeadlineSeconds: 60,
          template: {
            metadata: {
              labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "cronjob-name": input.name },
            },
            spec: {
              restartPolicy: "Never",
              containers: [
                {
                  name: "backup-retention",
                  image: "curlimages/curl:8.10.1",
                  imagePullPolicy: "IfNotPresent",
                  command: buildBackupRetentionCommand(input.orgId),
                  env: [
                    {
                      name: "BACKUP_CRON_API_KEY",
                      valueFrom: {
                        secretKeyRef: {
                          name: BACKUP_CRON_SECRET_NAME,
                          key: BACKUP_CRON_SECRET_KEY,
                        },
                      },
                    },
                  ],
                  resources: {
                    requests: { cpu: "10m", memory: "16Mi" },
                    limits: { cpu: "50m", memory: "32Mi" },
                  },
                },
              ],
            },
          },
        },
      },
    },
  };

  const result = await k8sRequest<CronJobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(input.namespace)}/cronjobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toScheduledJob(result.data) };
}

export async function deleteCronJob(
  namespace: string,
  name: string,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/cronjobs/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

// -------------------------------------------------------- Retention Purge
//
// Real, scheduled enforcement CronJob for lib/retention.ts's
// purgeExpiredAuditRows -- the distinct, sellable compliance control this
// capability's own rationale names: proof that stale
// platform_console.audit_log rows are purged automatically on a
// schedule, with a receipt, not retained forever or purged only by hand.
//
// Same shared-secret authentication pattern as COMPLIANCE_CRON_SECRET/
// EXPORT_SUBSCRIPTION_CRON_SECRET above (see createComplianceReportCronJob's
// header comment for the one-time operator provisioning step): the secret
// is injected via a real k8s `secretKeyRef` against a
// `platform-retention-purge-cron-secret` Secret this module never creates
// itself.
//
// One platform-wide CronJob, same shape as createExportSubscriptionCronJob
// -- platform_console.audit_log has no per-row org scoping (see
// lib/retention.ts's header comment), so there is no per-org CronJob to
// create; POST /api/cron/retention-purge purges the whole table against
// one retentionDays window every time it fires.
export const RETENTION_PURGE_CRON_SECRET_NAME = "platform-retention-purge-cron-secret";
export const RETENTION_PURGE_CRON_SECRET_KEY = "secret";
export const RETENTION_PURGE_CRON_JOB_NAME = "platform-retention-purge";
export const RETENTION_PURGE_CRON_JOB_LABEL = "retention-purge-cronjob";
// Fires once daily, off-peak -- a purge is a bulk DELETE across
// potentially many rows; running it once a day is ample for any
// day-granularity retentionDays window (the shortest configured tier
// default, `starter`'s 7 days, still has a full day of slack before a
// one-day-late firing could let a row live even one day past its window).
export const RETENTION_PURGE_CRON_SCHEDULE = "17 3 * * *";

function buildRetentionPurgeCronCommand(): string[] {
  return [
    "sh",
    "-c",
    `curl -sS -m 60 -X POST -H "x-retention-purge-cron-secret: $RETENTION_PURGE_CRON_SECRET" ` +
      `"http://platform-console.platform-console.svc.cluster.local/api/cron/retention-purge" && echo`,
  ];
}

/**
 * Creates the real, one-per-deployment recurring retention-purge CronJob
 * in the `platform-console` namespace. Idempotent from the caller's
 * perspective the same way createExportSubscriptionCronJob's own callers
 * are expected to be -- a second POST for the same fixed name 409s,
 * surfaced as a real `K8sResult` error, never silently swallowed.
 */
export async function createRetentionPurgeCronJob(): Promise<K8sResult<ScheduledJob>> {
  const manifest = {
    apiVersion: "batch/v1",
    kind: "CronJob",
    metadata: {
      name: RETENTION_PURGE_CRON_JOB_NAME,
      namespace: "platform-console",
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: RETENTION_PURGE_CRON_JOB_LABEL,
      },
    },
    spec: {
      schedule: RETENTION_PURGE_CRON_SCHEDULE,
      concurrencyPolicy: "Forbid",
      successfulJobsHistoryLimit: 3,
      failedJobsHistoryLimit: 3,
      jobTemplate: {
        spec: {
          backoffLimit: 0,
          activeDeadlineSeconds: 120,
          template: {
            metadata: {
              labels: {
                [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
                "cronjob-name": RETENTION_PURGE_CRON_JOB_NAME,
              },
            },
            spec: {
              restartPolicy: "Never",
              containers: [
                {
                  name: "retention-purge",
                  image: "curlimages/curl:8.10.1",
                  imagePullPolicy: "IfNotPresent",
                  command: buildRetentionPurgeCronCommand(),
                  env: [
                    {
                      name: "RETENTION_PURGE_CRON_SECRET",
                      valueFrom: {
                        secretKeyRef: {
                          name: RETENTION_PURGE_CRON_SECRET_NAME,
                          key: RETENTION_PURGE_CRON_SECRET_KEY,
                        },
                      },
                    },
                  ],
                  resources: {
                    requests: { cpu: "10m", memory: "16Mi" },
                    limits: { cpu: "50m", memory: "32Mi" },
                  },
                },
              ],
            },
          },
        },
      },
    },
  };

  const result = await k8sRequest<CronJobItem>(
    `/apis/batch/v1/namespaces/platform-console/cronjobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toScheduledJob(result.data) };
}
