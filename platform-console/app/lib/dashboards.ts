/**
 * Real Custom Dashboards / Saved Queries (AWS CloudWatch custom dashboards
 * / GCP Monitoring custom dashboards equivalent): an operator saves a real
 * query -- either PromQL against the real in-cluster Prometheus, or a
 * filtered lookup against the real durable audit log -- as a named,
 * reusable widget, then arranges several into a personal dashboard.
 *
 * Storage: one real k8s ConfigMap (`platform-console-dashboards`,
 * `platform-console` namespace), reusing the exact get-then-create-or-patch
 * primitive lib/k8s.ts's Feature Flags module established
 * (`getConfigMap`/`createOrUpdateConfigMap`) -- the same primitive
 * lib/budget-alerts.ts, lib/authz.ts, and lib/tags.ts already reuse for
 * their own ConfigMaps. No new k8s resource kind, no new RBAC verb: the
 * same `platform-console-feature-flags` Role (k8s/paas-rbac.yaml) already
 * grants get/list/create/update/patch on `configmaps` in this namespace
 * with no `resourceNames` restriction, so it already covers this ConfigMap
 * with zero YAML changes.
 *
 * Every widget is stored under key `widget.<uuid>` -> a JSON-encoded
 * Widget, one key per widget so a create/delete is a single-key RFC 7386
 * merge patch touching nothing else (same one-key-at-a-time convention
 * every ConfigMap-backed module in this console already follows).
 *
 * A widget is EXECUTED, never cached: executeWidget() below runs the
 * widget's real query against the real backend on every call --
 * lib/prometheus.ts's queryPrometheus for "promql" widgets,
 * lib/audit-db.ts's queryAuditLog for "audit-query" widgets -- and returns
 * whatever that backend returns right now. Nothing in this module ever
 * persists a query RESULT; only the query definition itself is durable.
 * That is what makes a dashboard reload a live re-query rather than a
 * frozen snapshot from creation time.
 *
 * Access level is per widget TYPE, matching exactly what the underlying
 * data source already requires of a direct query against it -- a
 * dashboard widget is just a saved lens onto data the viewer could already
 * query directly, never a privilege escalation past that:
 *   - "promql"      -> whatever /observability (app/api/prometheus/route.ts)
 *                       already requires: any authenticated session, no
 *                       extra role, and the exact same
 *                       ALLOWED_PROMETHEUS_QUERIES allowlist (lib/prometheus.ts)
 *                       -- a widget can never run a PromQL query that route
 *                       itself would refuse.
 *   - "audit-query"  -> whatever /audit (app/api/audit/route.ts) already
 *                       requires: requireRole(session, "owner").
 * WIDGET_TYPE_MIN_ROLE below is that per-type floor; minRoleForCreating
 * raises it to at least "member" (creating ANY widget, even a viewer-
 * accessible promql one, requires being a member) -- the exact same
 * "raise to at least member" shape lib/tags.ts's minRoleForTagging already
 * establishes for its own per-category minimums. minRoleForViewing returns
 * the per-type floor UNRAISED, so a dashboard load only ever executes a
 * widget the viewing session could reach the underlying data through
 * directly.
 */
import { randomUUID } from "crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { ALLOWED_PROMETHEUS_QUERIES, queryPrometheus } from "@/lib/prometheus";
import { queryAuditLog, type AuditLogRow } from "@/lib/audit-db";
import { ROLES, type Role } from "@/lib/authz";

export const DASHBOARDS_NAMESPACE = "platform-console";
export const DASHBOARDS_CONFIGMAP = "platform-console-dashboards";

export type WidgetType = "promql" | "audit-query";
export const WIDGET_TYPES: WidgetType[] = ["promql", "audit-query"];

function isWidgetType(value: string): value is WidgetType {
  return value === "promql" || value === "audit-query";
}

export interface Widget {
  id: string;
  title: string;
  type: WidgetType;
  query: string;
  createdBy: string;
  createdAt: string;
}

const WIDGET_TYPE_MIN_ROLE: Record<WidgetType, Role> = {
  promql: "viewer",
  "audit-query": "owner",
};

function roleMeets(role: Role, minimum: Role): boolean {
  return ROLES.indexOf(role) >= ROLES.indexOf(minimum);
}

/** The real minimum role required to CREATE a widget of this type -- at
 * least "member" (creating any saved widget, even a viewer-reachable
 * promql one, is a mutation), raised to that type's own
 * WIDGET_TYPE_MIN_ROLE when it is higher ("audit-query" -> "owner", same
 * as /audit itself). */
export function minRoleForCreating(type: WidgetType): Role {
  const typeMin = WIDGET_TYPE_MIN_ROLE[type];
  return ROLES.indexOf(typeMin) > ROLES.indexOf("member") ? typeMin : "member";
}

/** The real minimum role required to VIEW (execute) a widget of this type
 * -- exactly the per-type floor, unraised, so a dashboard load only ever
 * runs a query the viewing session's role already lets it run directly
 * against /observability or /audit. */
export function minRoleForViewing(type: WidgetType): Role {
  return WIDGET_TYPE_MIN_ROLE[type];
}

function widgetKey(id: string): string {
  return `widget.${id}`;
}

function parseWidget(id: string, raw: string): Widget | null {
  try {
    const p = JSON.parse(raw) as Partial<Widget>;
    if (
      typeof p.title === "string" &&
      typeof p.type === "string" &&
      isWidgetType(p.type) &&
      typeof p.query === "string" &&
      typeof p.createdBy === "string" &&
      typeof p.createdAt === "string"
    ) {
      return { id, title: p.title, type: p.type, query: p.query, createdBy: p.createdBy, createdAt: p.createdAt };
    }
    return null;
  } catch {
    return null;
  }
}

async function readAllWidgets(): Promise<K8sResult<Widget[]>> {
  const result = await getConfigMap(DASHBOARDS_NAMESPACE, DASHBOARDS_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};

  const widgets: Widget[] = [];
  for (const [key, raw] of Object.entries(data)) {
    if (!key.startsWith("widget.")) continue;
    const id = key.slice("widget.".length);
    const parsed = id ? parseWidget(id, raw) : null;
    if (parsed) widgets.push(parsed);
  }
  widgets.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ok: true, data: widgets };
}

/** Real list of every widget owned by `createdBy` -- a "personal
 * dashboard" is exactly this filter, never a separate per-user ConfigMap
 * or namespace. */
export async function listWidgets(createdBy: string): Promise<K8sResult<Widget[]>> {
  const result = await readAllWidgets();
  if (!result.ok) return result;
  return { ok: true, data: result.data.filter((w) => w.createdBy === createdBy) };
}

/** `null` when valid; otherwise a human-readable reason. Checked at create
 * time so an invalid widget is rejected with a clear 400 before it is ever
 * written to the ConfigMap, AND re-checked at execute time (executeWidget
 * below) so a ConfigMap edited by hand, or a future allowlist tightening,
 * can never be bypassed by a widget saved under looser rules. */
export function validateWidgetQuery(type: WidgetType, query: string): string | null {
  if (!query.trim()) return "query is required";
  if (type === "promql") {
    if (!ALLOWED_PROMETHEUS_QUERIES.has(query)) {
      return `PromQL query not in allowlist: ${[...ALLOWED_PROMETHEUS_QUERIES].join(", ")}`;
    }
    return null;
  }
  const parsed = parseAuditQuery(query);
  return "error" in parsed ? parsed.error : null;
}

export interface CreateWidgetInput {
  title: string;
  type: WidgetType;
  query: string;
  createdBy: string;
}

/** Real create via a single-key RFC 7386 merge patch (or create, on first
 * ever widget) -- same convention as every other ConfigMap-backed module
 * in this console. */
export async function createWidget(input: CreateWidgetInput): Promise<K8sResult<Widget>> {
  const title = input.title.trim();
  if (!title) return { ok: false, error: "title is required" };
  if (title.length > 120) return { ok: false, error: "title must be 120 characters or fewer" };
  if (!isWidgetType(input.type)) return { ok: false, error: `type must be one of: ${WIDGET_TYPES.join(", ")}` };
  const queryError = validateWidgetQuery(input.type, input.query);
  if (queryError) return { ok: false, error: queryError };

  const widget: Widget = {
    id: randomUUID(),
    title,
    type: input.type,
    query: input.query,
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
  };

  const result = await createOrUpdateConfigMap(DASHBOARDS_NAMESPACE, DASHBOARDS_CONFIGMAP, {
    [widgetKey(widget.id)]: JSON.stringify(widget),
  });
  if (!result.ok) return result;
  return { ok: true, data: widget };
}

/** Real delete via a single-key RFC 7386 merge patch setting that widget's
 * key to `null` -- ownership-checked: a widget can only ever be deleted by
 * the identifier that created it (a personal dashboard's widgets are not a
 * shared resource another operator may remove). Returns an explicit error
 * (never a silent no-op) when the widget doesn't exist or isn't owned by
 * `requestedBy`, so the API route can return a clear 404/403. */
export async function deleteWidget(id: string, requestedBy: string): Promise<K8sResult<null>> {
  const all = await readAllWidgets();
  if (!all.ok) return all;
  const widget = all.data.find((w) => w.id === id);
  if (!widget) return { ok: false, error: `widget '${id}' not found` };
  if (widget.createdBy !== requestedBy) {
    return { ok: false, error: `widget '${id}' is not owned by '${requestedBy}'` };
  }

  const result = await createOrUpdateConfigMap(DASHBOARDS_NAMESPACE, DASHBOARDS_CONFIGMAP, {
    [widgetKey(id)]: null,
  } as unknown as Record<string, string>);
  if (!result.ok) return result;
  return { ok: true, data: null };
}

// --------------------------------------------------------------- Execution

const AUDIT_QUERY_KEYS = new Set(["actor", "path", "from", "to", "window"]);
const WINDOW_RE = /^(\d+)(s|m|h|d)$/;
const WINDOW_UNIT_MS: Record<string, number> = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000 };
const AUDIT_QUERY_LIMIT = 100;

type ParsedAuditQuery =
  | { params: { actor?: string; path?: string; from?: string; to?: string; limit: number; offset: number } }
  | { error: string };

/**
 * The one query syntax "audit-query" widgets use: ordinary URL search
 * params, e.g. `actor=admin` or `actor=admin&window=1h`. `window` is a
 * relative lookback (`<n>(s|m|h|d)`) resolved to a fresh `from`/`to` pair
 * EVERY time the widget executes -- not stored as a fixed timestamp -- so
 * "over the last hour" always means the last hour as of THIS load, which
 * is exactly what makes a widget's audit-event count genuinely increase as
 * new matching events land, rather than being frozen at creation time.
 * `from`/`to` may also be given directly as RFC3339 timestamps for a fixed
 * historical range; `window` takes precedence over an explicit `from`/`to`
 * when both are present. Every param is passed straight through to
 * lib/audit-db.ts's queryAuditLog, which already parameterizes them (never
 * string-concatenated SQL) -- this function only shapes the params object.
 */
export function parseAuditQuery(query: string): ParsedAuditQuery {
  let params: URLSearchParams;
  try {
    params = new URLSearchParams(query);
  } catch {
    return { error: "audit-query must be a URL query string, e.g. actor=admin&window=1h" };
  }
  for (const key of params.keys()) {
    if (!AUDIT_QUERY_KEYS.has(key)) {
      return { error: `unknown audit-query param '${key}' -- allowed: ${[...AUDIT_QUERY_KEYS].join(", ")}` };
    }
  }

  const actor = params.get("actor")?.trim() || undefined;
  const path = params.get("path")?.trim() || undefined;
  const window = params.get("window")?.trim() || undefined;
  let from = params.get("from")?.trim() || undefined;
  let to = params.get("to")?.trim() || undefined;

  if (window) {
    const m = WINDOW_RE.exec(window);
    if (!m) return { error: `window must match <n>(s|m|h|d), e.g. "1h" -- got "${window}"` };
    const ms = Number(m[1]) * WINDOW_UNIT_MS[m[2]];
    const now = Date.now();
    from = new Date(now - ms).toISOString();
    to = new Date(now).toISOString();
  } else {
    if (from && Number.isNaN(Date.parse(from))) return { error: `from is not a valid timestamp: "${from}"` };
    if (to && Number.isNaN(Date.parse(to))) return { error: `to is not a valid timestamp: "${to}"` };
  }

  if (!actor && !path && !from && !to) {
    return { error: "audit-query must set at least one of actor, path, window, from, to" };
  }

  return { params: { actor, path, from, to, limit: AUDIT_QUERY_LIMIT, offset: 0 } };
}

export type WidgetExecutionResult =
  | { ok: true; type: "promql"; series: Array<{ metric: Record<string, string>; value: [number, string] }> }
  | { ok: true; type: "audit-query"; total: number; rows: AuditLogRow[] }
  | { ok: false; error: string };

/**
 * Runs `widget`'s real query against the REAL backend and returns whatever
 * it returns right now -- reuses lib/prometheus.ts's queryPrometheus and
 * lib/audit-db.ts's queryAuditLog exactly, no reimplementation of either
 * query path and no second, dashboard-only copy of the result shape.
 * Never caches, never persists the result -- call this fresh every time a
 * dashboard is rendered.
 */
export async function executeWidget(widget: Widget): Promise<WidgetExecutionResult> {
  if (widget.type === "promql") {
    const queryError = validateWidgetQuery("promql", widget.query);
    if (queryError) return { ok: false, error: queryError };
    const result = await queryPrometheus(widget.query);
    if (!result.ok) return { ok: false, error: result.error };
    const series = result.data.data?.result ?? [];
    return { ok: true, type: "promql", series: series.map((s) => ({ metric: s.metric, value: s.value })) };
  }

  const parsed = parseAuditQuery(widget.query);
  if ("error" in parsed) return { ok: false, error: parsed.error };
  const result = await queryAuditLog(parsed.params);
  if (!result.ok) return { ok: false, error: result.error };
  return { ok: true, type: "audit-query", total: result.data.total, rows: result.data.rows };
}
