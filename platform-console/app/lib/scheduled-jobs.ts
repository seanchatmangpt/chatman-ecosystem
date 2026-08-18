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
export type AllowedCommandId = "echo-timestamp" | "curl-status";

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
 * uses).
 */
export async function listCronJobs(namespace: string): Promise<K8sResult<ScheduledJob[]>> {
  const result = await k8sRequest<CronJobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/cronjobs?labelSelector=${encodeURIComponent(
      `${MANAGED_BY_LABEL}=${MANAGED_BY_VALUE}`,
    )}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toScheduledJob) };
}

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
