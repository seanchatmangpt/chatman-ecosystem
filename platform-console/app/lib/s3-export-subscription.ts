/**
 * Real "bring your own bucket" scheduled export subscription -- the
 * recurring, unattended counterpart to lib/export-all.ts (full tenant
 * bundle) and lib/audit-export.ts (audit-log NDJSON): both of those
 * already produce real export payloads but only ever hand them back as a
 * one-time browser download (POST /api/projects/[name]/export-all,
 * GET /api/audit/export). Enterprise data-governance / SIEM-ingestion
 * buyers need those same real payloads landing in THEIR OWN S3-compatible
 * bucket on a schedule with no human clicking a button -- the AWS
 * CloudTrail "S3 bucket delivery" / GCP "log sink to a customer bucket"
 * equivalent, one layer up from lib/scheduled-jobs.ts's own
 * compliance-report CronJob (which POSTs a report INTO this console; this
 * module instead PUTs a real object OUT to a bucket the customer owns and
 * controls, reachable via any S3-compatible endpoint -- AWS S3 itself, or
 * a self-hosted MinIO/Ceph/R2 endpoint the org points this at).
 *
 * Storage: one real k8s ConfigMap (`platform-console-export-subscriptions`,
 * `platform-console` namespace), one key per org id -> JSON
 * ExportSubscription -- identical get-then-create-or-patch
 * getConfigMap/createOrUpdateConfigMap primitive every other
 * ConfigMap-backed module in this repo already uses (lib/orgs.ts,
 * lib/approval-workflow.ts, lib/ip-allowlist.ts). One subscription per
 * org (not a list) -- same "the natural unit is the whole record for this
 * org" shape lib/orgs.ts's setOrgBranding/setOrgRegion already use, not a
 * per-run list (run HISTORY is its own separate ConfigMap key, see
 * `recordRunHistory` below, so history growth never risks corrupting the
 * subscription's own config row).
 *
 * Credentials-at-rest: this app has no pre-existing app-level encryption
 * helper (lib/ip-allowlist.ts and lib/orgs.ts's own "secrets" are CIDR
 * strings and org config, never credentials -- the only real secret
 * material this repo has previously stored is inside a k8s `Secret`
 * object itself, e.g. lib/api-keys.ts). A bucket access key is bearer
 * credential material that must never sit in a ConfigMap (world-readable
 * to anything with `get configmaps` RBAC) in cleartext, so this module
 * adds one small, real, symmetric encryption primitive
 * (`encryptSecret`/`decryptSecret`, AES-256-GCM via Node's built-in
 * `crypto` -- no new dependency) keyed by `process.env
 * .EXPORT_SUBSCRIPTION_ENCRYPTION_KEY` (a 32-byte key, hex-encoded, 64
 * hex chars -- provisioned the same one-time-operator-step way
 * lib/scheduled-jobs.ts's own header comment already discloses for
 * `COMPLIANCE_CRON_SECRET`). Fail CLOSED, not silently-plaintext: any
 * write attempted with no key configured, or any decrypt attempted with a
 * malformed/wrong key, returns a real error -- credentials are NEVER
 * persisted unencrypted and NEVER logged (writeAuditLogEntry callers in
 * the route only ever pass status codes/paths, never body content, same
 * discipline already used by every other route in this tree).
 */
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { createCipheriv, createDecipheriv, randomBytes, timingSafeEqual } from "crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { exportProjectBundle } from "@/lib/export-all";
import { streamAuditLogAsEcsNdjson } from "@/lib/audit-export";

export const EXPORT_SUBSCRIPTIONS_NAMESPACE = "platform-console";
export const EXPORT_SUBSCRIPTIONS_CONFIGMAP = "platform-console-export-subscriptions";
export const EXPORT_SUBSCRIPTION_RUNS_CONFIGMAP = "platform-console-export-subscription-runs";

export type ExportCadence = "daily" | "weekly";
export type ExportScope = "audit-log" | "full-export";
export type ExportRunStatus = "success" | "error";

const CADENCE_VALUES: ExportCadence[] = ["daily", "weekly"];
const SCOPE_VALUES: ExportScope[] = ["audit-log", "full-export"];

export function isExportCadence(value: string): value is ExportCadence {
  return (CADENCE_VALUES as string[]).includes(value);
}

export function isExportScope(value: string): value is ExportScope {
  return (SCOPE_VALUES as string[]).includes(value);
}

/** Real cron-schedule mapping -- same "documented schedule per cadence,
 * a fixed lookup table, never a free-text cron string a caller supplies"
 * discipline lib/compliance-report.ts's CADENCE_CRON_SCHEDULE already
 * establishes. Minute/hour deliberately off-the-hour (07/17), matching
 * this repo's own CronCreate-adjacent convention of not stacking every
 * scheduled thing on `:00`. */
export const EXPORT_SUBSCRIPTION_CRON_SCHEDULE: Record<ExportCadence, string> = {
  daily: "17 7 * * *",
  weekly: "17 7 * * 1",
};

export interface ExportSubscription {
  orgId: string;
  bucketEndpoint: string;
  bucketName: string;
  accessKeyIdEncrypted: string;
  secretAccessKeyEncrypted: string;
  prefix: string;
  cadence: ExportCadence;
  scope: ExportScope;
  enabled: boolean;
  lastRunAt: string | null;
  lastRunStatus: ExportRunStatus | null;
  updatedAt: string;
  updatedBy: string;
}

export interface ExportSubscriptionRun {
  runId: string;
  orgId: string;
  ranAt: string;
  status: ExportRunStatus;
  objectKey: string | null;
  bytesWritten: number | null;
  error: string | null;
}

// ------------------------------------------------------- Encryption

const ALGO = "aes-256-gcm";
const IV_LENGTH = 12; // recommended nonce length for GCM

function loadEncryptionKey(): Buffer | null {
  const hex = process.env.EXPORT_SUBSCRIPTION_ENCRYPTION_KEY;
  if (!hex || hex.length !== 64 || !/^[0-9a-fA-F]{64}$/.test(hex)) return null;
  return Buffer.from(hex, "hex");
}

/**
 * Real AES-256-GCM encrypt: fresh random 12-byte IV per call (never
 * reused -- GCM's own security proof requires a unique nonce per key),
 * output packed as `iv:authTag:ciphertext`, each hex-encoded, so the
 * whole thing round-trips as one ConfigMap-safe string. Returns `null`
 * when no valid 32-byte key is configured -- callers must treat that as
 * "reject the write", never persist plaintext as a fallback.
 */
export function encryptSecret(plaintext: string): string | null {
  const key = loadEncryptionKey();
  if (!key) return null;
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv(ALGO, key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  return `${iv.toString("hex")}:${authTag.toString("hex")}:${encrypted.toString("hex")}`;
}

/**
 * Real AES-256-GCM decrypt, the exact inverse of `encryptSecret`. Returns
 * `null` on any failure -- wrong/missing key, malformed packed string, or
 * a failed GCM auth-tag check (tampered ciphertext) -- never a partial or
 * best-effort plaintext.
 */
export function decryptSecret(packed: string): string | null {
  const key = loadEncryptionKey();
  if (!key) return null;
  const parts = packed.split(":");
  if (parts.length !== 3) return null;
  const [ivHex, tagHex, dataHex] = parts;
  try {
    const iv = Buffer.from(ivHex, "hex");
    const authTag = Buffer.from(tagHex, "hex");
    const data = Buffer.from(dataHex, "hex");
    const decipher = createDecipheriv(ALGO, key, iv);
    decipher.setAuthTag(authTag);
    const decrypted = Buffer.concat([decipher.update(data), decipher.final()]);
    return decrypted.toString("utf8");
  } catch {
    return null;
  }
}

export function isEncryptionConfigured(): boolean {
  return loadEncryptionKey() !== null;
}

// ------------------------------------------------------- Storage (config)

interface SubscriptionRegistry {
  [orgId: string]: ExportSubscription;
}

function isExportRunStatus(value: unknown): value is ExportRunStatus {
  return value === "success" || value === "error";
}

function isExportSubscription(value: unknown): value is ExportSubscription {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.orgId === "string" &&
    typeof v.bucketEndpoint === "string" &&
    typeof v.bucketName === "string" &&
    typeof v.accessKeyIdEncrypted === "string" &&
    typeof v.secretAccessKeyEncrypted === "string" &&
    typeof v.prefix === "string" &&
    typeof v.cadence === "string" &&
    isExportCadence(v.cadence) &&
    typeof v.scope === "string" &&
    isExportScope(v.scope) &&
    typeof v.enabled === "boolean" &&
    (v.lastRunAt === null || typeof v.lastRunAt === "string") &&
    (v.lastRunStatus === null || isExportRunStatus(v.lastRunStatus)) &&
    typeof v.updatedAt === "string" &&
    typeof v.updatedBy === "string"
  );
}

async function getRegistry(): Promise<K8sResult<SubscriptionRegistry>> {
  const existing = await getConfigMap(EXPORT_SUBSCRIPTIONS_NAMESPACE, EXPORT_SUBSCRIPTIONS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SubscriptionRegistry = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isExportSubscription(row)) parsed[orgId] = row;
      // A hand-edited/corrupt row is skipped, not fatal -- same "don't
      // let one bad row break the whole list" discipline lib/orgs.ts's
      // getRegistry and lib/approval-workflow.ts's getAll already use.
    } catch {
      // ignore -- malformed JSON for this key.
    }
  }
  return { ok: true, data: parsed };
}

/** Real read: backs GET .../export-subscription. Never returns the
 * decrypted credentials -- callers that need the plaintext for an actual
 * S3 PUT call `decryptSecret` themselves inside `runExportSubscription`,
 * never through this read path (which is what the route handler uses to
 * render the UI's config form). */
export async function getExportSubscription(orgId: string): Promise<K8sResult<ExportSubscription | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[orgId] ?? null };
}

export interface UpsertExportSubscriptionInput {
  orgId: string;
  bucketEndpoint: string;
  bucketName: string;
  accessKeyId: string;
  secretAccessKey: string;
  prefix: string;
  cadence: ExportCadence;
  scope: ExportScope;
  enabled: boolean;
  updatedBy: string;
}

/**
 * Real fail-closed input validation -- same discipline as
 * lib/orgs.ts's validateBranding: reject and return a specific string
 * error, never a fabricated silent default, so a bad value can never
 * reach the ConfigMap.
 *   - bucketEndpoint must be an `https://` URL (never plaintext http --
 *     credentials would traverse the wire unencrypted otherwise).
 *   - bucketName must be a valid S3-style bucket name (lowercase
 *     alphanumeric, dots, hyphens, 3-63 chars -- the real AWS S3 bucket
 *     naming constraint, https://docs.aws.amazon.com/AmazonS3/latest/
 *     userguide/bucketnamingrules.html -- also satisfied by every other
 *     S3-compatible implementation this targets, MinIO included).
 *   - prefix, if non-empty, must not start with `/` (S3 object keys are
 *     never rooted the way a filesystem path is).
 */
const BUCKET_NAME_RE = /^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$/;

export function validateExportSubscriptionInput(input: UpsertExportSubscriptionInput): string | null {
  if (!input.bucketEndpoint.startsWith("https://")) {
    return "bucketEndpoint must be an https:// URL";
  }
  if (!BUCKET_NAME_RE.test(input.bucketName)) {
    return "bucketName must be 3-63 chars, lowercase alphanumeric/dot/hyphen, matching S3 bucket naming rules";
  }
  if (!input.accessKeyId.trim()) {
    return "accessKeyId is required";
  }
  if (!input.secretAccessKey.trim()) {
    return "secretAccessKey is required";
  }
  if (input.prefix.startsWith("/")) {
    return "prefix must not start with '/'";
  }
  if (!isExportCadence(input.cadence)) {
    return "cadence must be 'daily' or 'weekly'";
  }
  if (!isExportScope(input.scope)) {
    return "scope must be 'audit-log' or 'full-export'";
  }
  return null;
}

/**
 * Real create-or-update write: backs POST .../export-subscription (after
 * the route's own maker-checker gate has already cleared -- see
 * app/api/orgs/[id]/export-subscription/route.ts). Encrypts both
 * credential fields via `encryptSecret` before they ever touch the
 * ConfigMap; returns a specific error (never a silent plaintext
 * fallback) when no encryption key is configured in this deployment.
 * Preserves `lastRunAt`/`lastRunStatus` from the existing row when one
 * exists -- editing bucket config does not erase run history, same
 * "merge-patch, don't clobber fields this write doesn't own" discipline
 * lib/orgs.ts's setOrgBranding/setOrgRegion already use.
 */
export async function upsertExportSubscription(
  input: UpsertExportSubscriptionInput,
): Promise<K8sResult<ExportSubscription> | { ok: false; error: string }> {
  const validationError = validateExportSubscriptionInput(input);
  if (validationError) return { ok: false, error: validationError };

  const accessKeyIdEncrypted = encryptSecret(input.accessKeyId);
  const secretAccessKeyEncrypted = encryptSecret(input.secretAccessKey);
  if (!accessKeyIdEncrypted || !secretAccessKeyEncrypted) {
    return {
      ok: false,
      error:
        "EXPORT_SUBSCRIPTION_ENCRYPTION_KEY is not configured (or malformed) on this deployment -- " +
        "credentials can never be stored unencrypted, so this write is refused",
    };
  }

  const existing = await getExportSubscription(input.orgId);
  if (!existing.ok) return existing;

  const subscription: ExportSubscription = {
    orgId: input.orgId,
    bucketEndpoint: input.bucketEndpoint,
    bucketName: input.bucketName,
    accessKeyIdEncrypted,
    secretAccessKeyEncrypted,
    prefix: input.prefix,
    cadence: input.cadence,
    scope: input.scope,
    enabled: input.enabled,
    lastRunAt: existing.data?.lastRunAt ?? null,
    lastRunStatus: existing.data?.lastRunStatus ?? null,
    updatedAt: new Date().toISOString(),
    updatedBy: input.updatedBy,
  };

  const result = await createOrUpdateConfigMap(EXPORT_SUBSCRIPTIONS_NAMESPACE, EXPORT_SUBSCRIPTIONS_CONFIGMAP, {
    [input.orgId]: JSON.stringify(subscription),
  });
  if (!result.ok) return result;
  return { ok: true, data: subscription };
}

async function patchLastRun(
  orgId: string,
  subscription: ExportSubscription,
  status: ExportRunStatus,
  ranAt: string,
): Promise<void> {
  const updated: ExportSubscription = { ...subscription, lastRunAt: ranAt, lastRunStatus: status };
  await createOrUpdateConfigMap(EXPORT_SUBSCRIPTIONS_NAMESPACE, EXPORT_SUBSCRIPTIONS_CONFIGMAP, {
    [orgId]: JSON.stringify(updated),
  });
}

// ------------------------------------------------------- Run history

interface RunHistoryRegistry {
  [orgId: string]: ExportSubscriptionRun[];
}

const MAX_RUNS_KEPT = 50;

function isExportSubscriptionRun(value: unknown): value is ExportSubscriptionRun {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.runId === "string" &&
    typeof v.orgId === "string" &&
    typeof v.ranAt === "string" &&
    isExportRunStatus(v.status) &&
    (v.objectKey === null || typeof v.objectKey === "string") &&
    (v.bytesWritten === null || typeof v.bytesWritten === "number") &&
    (v.error === null || typeof v.error === "string")
  );
}

async function getRunHistoryRegistry(): Promise<K8sResult<RunHistoryRegistry>> {
  const existing = await getConfigMap(EXPORT_SUBSCRIPTIONS_NAMESPACE, EXPORT_SUBSCRIPTION_RUNS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: RunHistoryRegistry = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[orgId] = rows.filter(isExportSubscriptionRun);
      }
    } catch {
      // ignore -- malformed JSON for this key.
    }
  }
  return { ok: true, data: parsed };
}

/** Real per-run audit trail: backs the UI's run-history log. Most recent
 * run first. `[]` for an org that has never run, same "empty is not an
 * error" convention every other list-read in this module uses. */
export async function listExportSubscriptionRuns(orgId: string): Promise<K8sResult<ExportSubscriptionRun[]>> {
  const registry = await getRunHistoryRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: (registry.data[orgId] ?? []).slice().reverse() };
}

/** Appends one real run record, capped to the most recent `MAX_RUNS_KEPT`
 * -- an unbounded per-org run log would eventually make the ConfigMap
 * value exceed k8s's 1MiB total-size ceiling for a daily/weekly cadence
 * running indefinitely; 50 runs is >6 weeks of daily history, ample for
 * the run-history log's own stated purpose (recent troubleshooting, not
 * an unbounded archive -- lib/audit-export.ts's durable audit_log table
 * remains the system of record for anything longer-lived). */
async function recordRunHistory(orgId: string, run: ExportSubscriptionRun): Promise<void> {
  const registry = await getRunHistoryRegistry();
  const existingRuns = registry.ok ? (registry.data[orgId] ?? []) : [];
  const updated = [...existingRuns, run].slice(-MAX_RUNS_KEPT);
  await createOrUpdateConfigMap(EXPORT_SUBSCRIPTIONS_NAMESPACE, EXPORT_SUBSCRIPTION_RUNS_CONFIGMAP, {
    [orgId]: JSON.stringify(updated),
  });
}

// ------------------------------------------------------- Execution

/**
 * Builds the real export payload for one subscription's configured
 * `scope`, reusing the exact existing generators this capability exists
 * to schedule -- never a re-implementation:
 *   - "audit-log": lib/audit-export.ts's streamAuditLogAsEcsNdjson (the
 *     same NDJSON GET /api/audit/export already produces), joined into
 *     one buffer since a single S3 PutObjectCommand needs one body.
 *   - "full-export": lib/export-all.ts's exportProjectBundle -- called
 *     with `orgId` as the project name, matching every other
 *     `/api/orgs/[id]/*` route's own "id resolves via the registry, or
 *     id IS the namespace/target" convention documented throughout this
 *     tree (see compliance-reports/route.ts's header comment).
 */
async function buildPayload(
  orgId: string,
  scope: ExportScope,
): Promise<{ ok: true; data: { body: Buffer; filename: string } } | { ok: false; error: string }> {
  if (scope === "audit-log") {
    try {
      const lines: string[] = [];
      for await (const line of streamAuditLogAsEcsNdjson({})) {
        lines.push(line);
      }
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      return {
        ok: true,
        data: { body: Buffer.from(lines.join("")), filename: `audit-log-${orgId}-${stamp}.ndjson` },
      };
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : String(err) };
    }
  }

  const bundleResult = await exportProjectBundle(orgId);
  if (!bundleResult.ok) return bundleResult;
  return { ok: true, data: { body: bundleResult.data.archive, filename: bundleResult.data.filename } };
}

function buildObjectKey(prefix: string, filename: string): string {
  const cleanPrefix = prefix.replace(/\/+$/, "");
  return cleanPrefix ? `${cleanPrefix}/${filename}` : filename;
}

/**
 * The real PUT: constructs a real `S3Client` pointed at this
 * subscription's own `bucketEndpoint` (any S3-compatible endpoint --
 * AWS S3 itself, or a self-hosted MinIO/Ceph/R2 endpoint the org
 * configured) with `forcePathStyle: true` (required for most
 * non-AWS S3-compatible endpoints, including MinIO, to resolve
 * `<endpoint>/<bucket>/<key>` instead of AWS's own
 * `<bucket>.<endpoint>/<key>` virtual-hosted-style default -- harmless
 * against real AWS S3 too), decrypts the stored credentials via
 * `decryptSecret` (never logged, never returned to any caller), and
 * issues one real `PutObjectCommand`.
 */
async function putToBucket(
  subscription: ExportSubscription,
  body: Buffer,
  objectKey: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  const accessKeyId = decryptSecret(subscription.accessKeyIdEncrypted);
  const secretAccessKey = decryptSecret(subscription.secretAccessKeyEncrypted);
  if (!accessKeyId || !secretAccessKey) {
    return {
      ok: false,
      error:
        "failed to decrypt stored bucket credentials -- EXPORT_SUBSCRIPTION_ENCRYPTION_KEY missing/changed since this subscription was saved",
    };
  }

  try {
    const client = new S3Client({
      endpoint: subscription.bucketEndpoint,
      region: "us-east-1", // required by the SDK even for non-AWS endpoints; ignored by most S3-compatible servers (MinIO included)
      forcePathStyle: true,
      credentials: { accessKeyId, secretAccessKey },
    });
    await client.send(
      new PutObjectCommand({
        Bucket: subscription.bucketName,
        Key: objectKey,
        Body: body,
        ContentType: objectKey.endsWith(".ndjson") ? "application/x-ndjson" : "application/zip",
      }),
    );
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * The real end-to-end run: build the payload (reusing export-all.ts /
 * audit-export.ts unchanged), PUT it to the org's own configured bucket,
 * then record BOTH the subscription's own `lastRunAt`/`lastRunStatus`
 * (for the config view) and one entry in the separate run-history log
 * (for the UI's per-run audit trail) -- always, on both success and
 * failure, so a run that fails to reach the bucket is exactly as visible
 * as one that succeeds, never silently dropped.
 */
export async function runExportSubscription(
  orgId: string,
): Promise<{ ok: true; data: ExportSubscriptionRun } | { ok: false; error: string }> {
  const subResult = await getExportSubscription(orgId);
  if (!subResult.ok) return subResult;
  if (!subResult.data) return { ok: false, error: `no export subscription configured for org '${orgId}'` };
  const subscription = subResult.data;

  const ranAt = new Date().toISOString();
  const runId = globalThis.crypto.randomUUID();

  const payloadResult = await buildPayload(orgId, subscription.scope);
  if (!payloadResult.ok) {
    const run: ExportSubscriptionRun = {
      runId,
      orgId,
      ranAt,
      status: "error",
      objectKey: null,
      bytesWritten: null,
      error: payloadResult.error,
    };
    await Promise.all([patchLastRun(orgId, subscription, "error", ranAt), recordRunHistory(orgId, run)]);
    return { ok: true, data: run };
  }

  const objectKey = buildObjectKey(subscription.prefix, payloadResult.data.filename);
  const putResult = await putToBucket(subscription, payloadResult.data.body, objectKey);

  const run: ExportSubscriptionRun = {
    runId,
    orgId,
    ranAt,
    status: putResult.ok ? "success" : "error",
    objectKey: putResult.ok ? objectKey : null,
    bytesWritten: putResult.ok ? payloadResult.data.body.length : null,
    error: putResult.ok ? null : putResult.error,
  };
  await Promise.all([
    patchLastRun(orgId, subscription, run.status, ranAt),
    recordRunHistory(orgId, run),
  ]);
  return { ok: true, data: run };
}

/**
 * Real "is this subscription due right now" check, called by the cron
 * endpoint (POST .../export-subscription with the cron shared-secret --
 * see the route's own header comment) for every enabled subscription.
 * `daily` is due once `lastRunAt` is more than 20 hours old (not a flat
 * 24h -- a poll/cron interval always drifts a little; 20h keeps a
 * same-day-ish trigger from being starved by a slightly-early previous
 * run), `weekly` once it is more than 6.5 days old, matching the same
 * "trailing window with headroom, not an exact boundary" discipline
 * lib/budget-alerts.ts's own BUDGET_WINDOW_HOURS documents. A
 * subscription that has never run (`lastRunAt === null`) is always due.
 */
export function isSubscriptionDue(subscription: ExportSubscription, now: Date = new Date()): boolean {
  if (!subscription.enabled) return false;
  if (!subscription.lastRunAt) return true;
  const elapsedHours = (now.getTime() - Date.parse(subscription.lastRunAt)) / (1000 * 60 * 60);
  const thresholdHours = subscription.cadence === "daily" ? 20 : 6.5 * 24;
  return elapsedHours >= thresholdHours;
}

/**
 * Runs every enabled, due subscription across every org (the real cron
 * fan-out lib/scheduled-jobs.ts's CronJob curls into via the route's
 * cron-secret path). Failures for one org never block another --
 * matches export-all.ts's own "one warning per failed part, never a
 * whole-request abort" posture, scaled up to "one org's failure never
 * blocks the next org's run".
 */
export async function runDueExportSubscriptions(): Promise<
  K8sResult<{ ranOrgIds: string[]; skippedOrgIds: string[] }>
> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const ranOrgIds: string[] = [];
  const skippedOrgIds: string[] = [];
  for (const [orgId, subscription] of Object.entries(registry.data)) {
    if (!isSubscriptionDue(subscription)) {
      skippedOrgIds.push(orgId);
      continue;
    }
    await runExportSubscription(orgId);
    ranOrgIds.push(orgId);
  }
  return { ok: true, data: { ranOrgIds, skippedOrgIds } };
}

/** Real constant-time cron-secret comparison, same shape as every other
 * "compare a presented shared secret" check would want -- guards against
 * a timing side-channel on the comparison itself (belt-and-suspenders;
 * the route's own `isCronAuthenticated` uses this rather than `===`). */
export function safeCompareSecret(presented: string, expected: string): boolean {
  const presentedBuf = Buffer.from(presented);
  const expectedBuf = Buffer.from(expected);
  if (presentedBuf.length !== expectedBuf.length) return false;
  return timingSafeEqual(presentedBuf, expectedBuf);
}
