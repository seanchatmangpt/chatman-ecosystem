/**
 * Real, append-only customer-facing API deprecation-notice feed --
 * distinct from lib/changelog.ts's tier-scoped product changelog.
 * lib/changelog.ts documents UI/feature announcements gated by
 * `ProjectTier` (see that module's own header comment); this module
 * documents REST API *contract lifecycle* -- which endpoint+method pairs
 * are sunsetting, when, and what an integrating client should migrate to.
 * Standard enterprise-API-vendor surface (cf. Stripe's own API
 * changelog/deprecation feed) this repo did not yet have: enterprise
 * consumers building integrations against this platform's REST endpoints
 * (see app/api/v1/*) need a machine-readable, versioned deprecation
 * schedule to plan their own engineering work around, not a UI-only
 * announcement.
 *
 * Storage: one real k8s ConfigMap (`platform-api-deprecations`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/freeze-windows.ts,
 * lib/ip-allowlist.ts, lib/authz.ts) already uses -- no new k8s resource
 * kind, no new RBAC verb: the same `platform-console-feature-flags` Role
 * already grants get/list/create/update/patch on `configmaps` in this
 * namespace with no `resourceNames` restriction.
 *
 * Single key (`entries`) holds the whole JSON array -- append-only: this
 * module only ever adds a new notice via `appendApiDeprecation`, it never
 * exposes an update or delete primitive, so a sunset date once announced
 * cannot silently move or vanish from the feed (an enterprise consumer
 * who already planned migration work off a published notice must be able
 * to trust it stays published).
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const API_DEPRECATIONS_NAMESPACE = "platform-console";
export const API_DEPRECATIONS_CONFIGMAP = "platform-api-deprecations";

export type ApiDeprecationSeverity = "info" | "breaking";

export const API_DEPRECATION_METHODS = [
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
] as const;
export type ApiDeprecationMethod = (typeof API_DEPRECATION_METHODS)[number];

export interface ApiDeprecationEntry {
  id: string;
  /** Path pattern of the deprecated endpoint, e.g. "/api/v1/projects/:name". */
  endpointPattern: string;
  method: ApiDeprecationMethod;
  /** ISO 8601 date (YYYY-MM-DD) this deprecation notice was published. */
  announcedAt: string;
  /** ISO 8601 date (YYYY-MM-DD) this endpoint stops being served. */
  sunsetDate: string;
  /** Endpoint pattern integrators should migrate to, or null if this
   *  capability is being removed outright with no direct replacement. */
  replacementEndpoint: string | null;
  migrationNote: string;
  severity: ApiDeprecationSeverity;
  createdBy: string;
  createdAt: string;
}

export interface ApiDeprecationInput {
  endpointPattern: string;
  method: ApiDeprecationMethod;
  announcedAt: string;
  sunsetDate: string;
  replacementEndpoint: string | null;
  migrationNote: string;
  severity: ApiDeprecationSeverity;
}

function isIsoDate(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(value))
  );
}

function isApiDeprecationEntry(value: unknown): value is ApiDeprecationEntry {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.endpointPattern === "string" &&
    v.endpointPattern.length > 0 &&
    (API_DEPRECATION_METHODS as readonly string[]).includes(v.method as string) &&
    isIsoDate(v.announcedAt) &&
    isIsoDate(v.sunsetDate) &&
    (v.replacementEndpoint === null || typeof v.replacementEndpoint === "string") &&
    typeof v.migrationNote === "string" &&
    (v.severity === "info" || v.severity === "breaking") &&
    typeof v.createdBy === "string" &&
    typeof v.createdAt === "string"
  );
}

/**
 * Validates a POST body's shape/content before it is appended. Returns a
 * human-readable error string on the first violation found, or `null` if
 * the input is valid -- same convention as
 * lib/freeze-windows.ts's validateFreezeWindowInput.
 */
export function validateApiDeprecationInput(input: {
  endpointPattern: string;
  method: string;
  announcedAt: string;
  sunsetDate: string;
  replacementEndpoint: string | null;
  migrationNote: string;
  severity: string;
}): string | null {
  if (!input.endpointPattern) return "endpointPattern is required";
  if (!input.endpointPattern.startsWith("/")) {
    return "endpointPattern must be an absolute path starting with '/'";
  }
  if (!(API_DEPRECATION_METHODS as readonly string[]).includes(input.method)) {
    return `method must be one of: ${API_DEPRECATION_METHODS.join(", ")}`;
  }
  if (!isIsoDate(input.announcedAt)) {
    return "announcedAt must be an ISO 8601 date (YYYY-MM-DD)";
  }
  if (!isIsoDate(input.sunsetDate)) {
    return "sunsetDate must be an ISO 8601 date (YYYY-MM-DD)";
  }
  if (Date.parse(input.sunsetDate) < Date.parse(input.announcedAt)) {
    return "sunsetDate must not be before announcedAt";
  }
  if (input.replacementEndpoint !== null && typeof input.replacementEndpoint !== "string") {
    return "replacementEndpoint must be a string or null";
  }
  if (!input.migrationNote) return "migrationNote is required";
  if (input.severity !== "info" && input.severity !== "breaking") {
    return "severity must be 'info' or 'breaking'";
  }
  return null;
}

function parseEntries(raw: string | undefined): ApiDeprecationEntry[] {
  if (!raw) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  return parsed.filter(isApiDeprecationEntry);
}

/**
 * Lists every published deprecation notice, oldest-announced first as
 * stored -- callers that need `active`-only filtering or `sunsetDate`
 * ordering (GET /api/api-deprecations's `?active=true`) apply that on
 * top of this raw list, same "storage returns everything, the route
 * shapes the response" split lib/freeze-windows.ts's listFreezeWindows
 * already uses.
 */
export async function listApiDeprecations(): Promise<K8sResult<ApiDeprecationEntry[]>> {
  const result = await getConfigMap(API_DEPRECATIONS_NAMESPACE, API_DEPRECATIONS_CONFIGMAP);
  if (!result.ok) return result;
  if (!result.data) return { ok: true, data: [] };
  return { ok: true, data: parseEntries(result.data.data?.entries) };
}

/**
 * Appends one new deprecation notice to the ConfigMap-backed array.
 * Read-then-write against the live ConfigMap (no in-process cache) so
 * two concurrent admin POSTs both land -- same last-writer-wins-on-the-
 * whole-array tradeoff lib/freeze-windows.ts's createFreezeWindow already
 * accepts for this class of low-frequency admin mutation.
 */
export async function appendApiDeprecation(
  input: ApiDeprecationInput & { createdBy: string },
): Promise<K8sResult<ApiDeprecationEntry>> {
  const existing = await listApiDeprecations();
  if (!existing.ok) return existing;

  const entry: ApiDeprecationEntry = {
    id: `apidep-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    endpointPattern: input.endpointPattern,
    method: input.method,
    announcedAt: input.announcedAt,
    sunsetDate: input.sunsetDate,
    replacementEndpoint: input.replacementEndpoint,
    migrationNote: input.migrationNote,
    severity: input.severity,
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
  };

  const next = [...existing.data, entry];
  const result = await createOrUpdateConfigMap(API_DEPRECATIONS_NAMESPACE, API_DEPRECATIONS_CONFIGMAP, {
    entries: JSON.stringify(next),
  });
  if (!result.ok) return result;
  return { ok: true, data: entry };
}

/**
 * Filters to entries whose `sunsetDate` is still in the future (strictly
 * after `now`) and sorts by `sunsetDate` ascending -- the exact shape
 * GET /api/api-deprecations?active=true returns, so an external API
 * client or status-page widget can render "what's coming next" directly.
 */
export function activeApiDeprecations(
  entries: ApiDeprecationEntry[],
  now: Date = new Date(),
): ApiDeprecationEntry[] {
  const nowTime = now.getTime();
  return entries
    .filter((entry) => Date.parse(entry.sunsetDate) > nowTime)
    .sort((a, b) => a.sunsetDate.localeCompare(b.sunsetDate));
}
