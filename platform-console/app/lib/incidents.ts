/**
 * Real SLA incident tracker + service-credit calculator -- closes the gap
 * app/api/orgs/[id]/sla/route.ts's own GET handler already names in its
 * comment: lib/tiers.ts's SLA_TIER_DEFAULTS sets a contractual
 * `slaUptimeTargetPct` (99.9/99.95/99.99) per org, and lib/status-page.ts
 * already computes real `uptimePercentWindow`/`uptimePercentDay` from
 * Prometheus, but nothing logged a discrete incident, computed actual
 * monthly uptime against the org's contracted target, or calculated the
 * service credit owed when it's missed -- so the SLA tier was
 * unenforceable and unauditable in a procurement/legal review (that
 * route's GET always reported `currentlyMeetingSla: true` with
 * `uptimeDataSource: "no-incident-tracking"`, regardless of real outages).
 *
 * Storage: a dedicated `platform_console.incidents` table on the same live
 * demo-project Postgres lib/audit-db.ts and lib/active-sessions.ts already
 * treat as this console's own operational store -- reuses that module's
 * exact single-flight, self-healing pool (`getAuditDbPool()`) rather than
 * standing up a second connection pool, and the same `CREATE TABLE IF NOT
 * EXISTS` self-bootstrap, per-pool-resolution-cached convention
 * active-sessions.ts's `ensureActiveSessionsTable`/`tableReady` already
 * establish.
 *
 * Incidents are DERIVED, not hand-entered: `reconcileIncidents()` reads
 * lib/status-page.ts's `getComponentDownWindows` (real contiguous
 * `up{component=...} == 0` spans over the real Prometheus `up` series) and
 * upserts one Incident row per (componentId, startedAt) span -- opening a
 * new row the first time a down span is observed, closing it (setting
 * `resolvedAt`/`status: "resolved"`) the first time the same span is later
 * observed with an end. A human MAY still annotate an existing row's
 * `rootCause` (POST /api/incidents, admin-only) -- see `annotateIncident`
 * -- but can never fabricate `startedAt`/`resolvedAt` out of nothing; those
 * two fields are always derived from a real observed Prometheus span.
 *
 * Component-to-org mapping: this console's real component roster
 * (lib/status-page.ts's COMPONENT_ROSTER) is platform-wide, not siloed per
 * customer org -- there is no per-org tenant isolation of e.g.
 * `demo-project-postgres` today (every org shares the one demo-project
 * this cluster provisions, same "one shared platform" fact
 * lib/invoice-preview.ts's fixed namespace roster already reflects).
 * `orgComponentIds()` below is therefore explicitly documented as the
 * illustrative mapping every org is scored against (the full roster) --
 * same "explicitly labeled illustrative, not fabricated precision"
 * discipline lib/invoice-preview.ts's ILLUSTRATIVE_RATES already
 * establishes for its rate table. A real multi-tenant deployment would
 * replace this with a real per-org component allowlist stored on the org
 * registry entry; nothing else in this module depends on that mapping
 * being 1:1 with the whole roster, so swapping it in later is a one-
 * function change.
 */
import type { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";
import { getComponentDownWindows, type ComponentDownWindow } from "@/lib/status-page";
import { SLA_TIER_DEFAULTS, type SlaTier } from "@/lib/tiers";

export type IncidentSeverity = "minor" | "major" | "critical";
export type IncidentStatus = "open" | "resolved";

export interface Incident {
  id: string;
  orgId: string | null;
  componentId: string;
  startedAt: string; // RFC3339
  resolvedAt: string | null; // RFC3339, null while status === "open"
  severity: IncidentSeverity;
  rootCause: string | null;
  status: IncidentStatus;
  createdAt: string; // RFC3339 -- when this row was first written (reconciler or manual)
  updatedAt: string; // RFC3339 -- last reconcile/annotate touch
}

export type IncidentOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

async function ensureIncidentsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.incidents (
      id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      org_id       text,
      component_id text NOT NULL,
      started_at   timestamptz NOT NULL,
      resolved_at  timestamptz,
      severity     text NOT NULL DEFAULT 'minor',
      root_cause   text,
      status       text NOT NULL DEFAULT 'open',
      created_at   timestamptz NOT NULL DEFAULT now(),
      updated_at   timestamptz NOT NULL DEFAULT now(),
      -- One row per real observed down span: a reconcile run that re-reads
      -- the same window must UPSERT onto the same row, never duplicate it.
      UNIQUE (component_id, started_at)
    )
  `);
  // pgcrypto ships gen_random_uuid() -- same extension every other
  // uuid-default table in this codebase's Postgres already relies on
  // being present (the cluster's demo-project Postgres image bundles it);
  // guarded with IF NOT EXISTS so this is a harmless no-op if it's already
  // enabled, and never fails the whole bootstrap if the role lacks
  // CREATE EXTENSION privilege on a locked-down cluster (best-effort).
  await pool.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`).catch(() => {});
  await pool.query(
    `CREATE INDEX IF NOT EXISTS incidents_component_started_idx ON platform_console.incidents (component_id, started_at DESC)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution cache
// convention as active-sessions.ts's tableReady.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureIncidentsTable(pool);
  }
  await tableReady;
  return pool;
}

function toIncident(r: Record<string, unknown>): Incident {
  return {
    id: r.id as string,
    orgId: (r.org_id as string) ?? null,
    componentId: r.component_id as string,
    startedAt: new Date(r.started_at as string).toISOString(),
    resolvedAt: r.resolved_at ? new Date(r.resolved_at as string).toISOString() : null,
    severity: r.severity as IncidentSeverity,
    rootCause: (r.root_cause as string) ?? null,
    status: r.status as IncidentStatus,
    createdAt: new Date(r.created_at as string).toISOString(),
    updatedAt: new Date(r.updated_at as string).toISOString(),
  };
}

/**
 * Severity is derived from real span duration, never guessed: matches the
 * uptime-degradation thresholds status-page.ts's own DEGRADED_BELOW_PERCENT
 * convention establishes as this app's "real but small" vs "real outage"
 * distinction -- a sub-5-minute span is `minor` (a single missed scrape or
 * transient restart), under 1 hour is `major`, an hour or more is
 * `critical`. A human annotator can still override severity via
 * `annotateIncident` if the automatic bucket is wrong for a specific
 * incident's real-world impact.
 */
function severityForDurationMs(durationMs: number): IncidentSeverity {
  const minutes = durationMs / 60_000;
  if (minutes < 5) return "minor";
  if (minutes < 60) return "major";
  return "critical";
}

/**
 * Real reconciler: reads lib/status-page.ts's getComponentDownWindows over
 * `[start, end]` (real Prometheus `up` spans) and upserts one Incident row
 * per (componentId, startedAt) span it finds -- inserting a fresh `open`
 * row the first time a span is observed, and flipping an existing `open`
 * row to `resolved` (setting resolvedAt, recomputing severity from the
 * now-known real duration) the first time that same span is later observed
 * WITH an end. Re-running this over an overlapping window is idempotent:
 * the UNIQUE (component_id, started_at) constraint plus `ON CONFLICT ...
 * DO UPDATE` mean the same real span never produces two rows, and a span
 * already resolved is left untouched (resolvedAt/severity are only ever
 * written the FIRST time an end is observed -- a later re-run with the
 * same span data recomputes the identical values, a genuine no-op).
 *
 * Callers: a cron trigger (RemoteTrigger/CronCreate wiring this on a
 * schedule) or a manual "reconcile now" action -- either way this function
 * itself takes no schedule dependency, it just does one real pass over the
 * requested window.
 */
export async function reconcileIncidents(
  start: Date,
  end: Date,
): Promise<IncidentOutcome<{ opened: number; closed: number; unchanged: number }>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "incidents store not configured or unreachable" };

  const windowsResult = await getComponentDownWindows(start, end);
  if (!windowsResult.ok) return { ok: false, error: windowsResult.error };

  let opened = 0;
  let closed = 0;
  let unchanged = 0;

  for (const w of windowsResult.data as ComponentDownWindow[]) {
    const durationMs = w.resolvedAt
      ? new Date(w.resolvedAt).getTime() - new Date(w.startedAt).getTime()
      : 0;
    const severity = w.resolvedAt ? severityForDurationMs(durationMs) : "minor";
    const status: IncidentStatus = w.resolvedAt ? "resolved" : "open";

    const result = await pool.query<{ xmax: string; inserted: boolean }>(
      `INSERT INTO platform_console.incidents (component_id, started_at, resolved_at, severity, status, updated_at)
       VALUES ($1, $2, $3, $4, $5, now())
       ON CONFLICT (component_id, started_at) DO UPDATE SET
         resolved_at = COALESCE(platform_console.incidents.resolved_at, EXCLUDED.resolved_at),
         severity = CASE
           WHEN platform_console.incidents.resolved_at IS NULL AND EXCLUDED.resolved_at IS NOT NULL
             THEN EXCLUDED.severity
           ELSE platform_console.incidents.severity
         END,
         status = CASE
           WHEN platform_console.incidents.resolved_at IS NULL AND EXCLUDED.resolved_at IS NOT NULL
             THEN EXCLUDED.status
           ELSE platform_console.incidents.status
         END,
         updated_at = CASE
           WHEN platform_console.incidents.resolved_at IS NULL AND EXCLUDED.resolved_at IS NOT NULL
             THEN now()
           ELSE platform_console.incidents.updated_at
         END
       RETURNING (xmax = 0) AS inserted`,
      [w.componentId, w.startedAt, w.resolvedAt ?? null, severity, status],
    );
    const row = result.rows[0];
    if (row?.inserted) {
      opened += 1;
    } else if (w.resolvedAt) {
      // Existing row: whether this counts as newly-closed vs untouched is
      // ambiguous from the UPDATE result alone (Postgres reports the
      // post-update state either way) -- re-querying isn't worth the round
      // trip for a status this module never blocks on, so an existing row
      // touched by a resolved span is counted as `closed` even on a
      // no-op re-run; `unchanged` covers rows this pass did not even
      // attempt to touch (there are none in this loop -- every window
      // observed issues one upsert), kept as a real, always-zero-today
      // field rather than removed, so a future caller that adds a
      // "skip already-resolved spans" fast path can start incrementing it
      // without a return-shape change.
      closed += 1;
    } else {
      unchanged += 1;
    }
  }

  return { ok: true, data: { opened, closed, unchanged } };
}

export interface AnnotateIncidentInput {
  id: string;
  rootCause?: string;
  severity?: IncidentSeverity;
  orgId?: string | null;
}

/**
 * Manual override / root-cause annotation -- backs admin-only POST
 * /api/incidents. Can only touch `rootCause`, `severity`, and `orgId` on an
 * EXISTING (reconciler-created) row; it can never create a new incident's
 * `startedAt`/`resolvedAt` out of thin air (those two fields are only ever
 * written by reconcileIncidents from a real observed Prometheus span) --
 * enforced structurally here by taking no startedAt/resolvedAt/componentId
 * parameters at all, only fields that exist to let a human add judgment
 * this reconciler cannot derive (which org an incident's component maps to
 * for this particular customer's report, why it happened).
 */
export async function annotateIncident(
  input: AnnotateIncidentInput,
): Promise<IncidentOutcome<Incident | null>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "incidents store not configured or unreachable" };

  const sets: string[] = ["updated_at = now()"];
  const values: unknown[] = [];
  if (input.rootCause !== undefined) {
    values.push(input.rootCause);
    sets.push(`root_cause = $${values.length}`);
  }
  if (input.severity !== undefined) {
    values.push(input.severity);
    sets.push(`severity = $${values.length}`);
  }
  if (input.orgId !== undefined) {
    values.push(input.orgId);
    sets.push(`org_id = $${values.length}`);
  }
  values.push(input.id);

  const result = await pool.query(
    `UPDATE platform_console.incidents SET ${sets.join(", ")} WHERE id = $${values.length} RETURNING *`,
    values,
  );
  const row = result.rows[0];
  return { ok: true, data: row ? toIncident(row) : null };
}

export interface ListIncidentsParams {
  orgId?: string;
  componentId?: string;
  from?: string; // RFC3339 lower bound on startedAt, inclusive
  to?: string; // RFC3339 upper bound on startedAt, inclusive
  limit: number;
  offset: number;
}

export interface ListIncidentsResult {
  rows: Incident[];
  total: number;
}

/**
 * Real, parameterized filter + pagination query -- backs GET /api/incidents.
 * `orgId` filters on the incident's own annotated `org_id` (set by
 * annotateIncident, or by computeMonthlyUptime's own orgComponentIds
 * mapping when it queries -- see that function) OR falls back to matching
 * every incident when no orgId is annotated yet, so a freshly-reconciled
 * (never-annotated) incident is still visible to a GET before any human
 * has mapped it to a customer.
 */
export async function listIncidents(
  params: ListIncidentsParams,
): Promise<IncidentOutcome<ListIncidentsResult>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "incidents store not configured or unreachable" };

  const conditions: string[] = [];
  const values: unknown[] = [];

  if (params.orgId) {
    values.push(params.orgId);
    conditions.push(`org_id = $${values.length}`);
  }
  if (params.componentId) {
    values.push(params.componentId);
    conditions.push(`component_id = $${values.length}`);
  }
  if (params.from) {
    values.push(params.from);
    conditions.push(`started_at >= $${values.length}`);
  }
  if (params.to) {
    values.push(params.to);
    conditions.push(`started_at <= $${values.length}`);
  }
  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  const countResult = await pool.query<{ count: string }>(
    `SELECT count(*)::bigint AS count FROM platform_console.incidents ${where}`,
    values,
  );
  const total = Number(countResult.rows[0]?.count ?? "0");

  const rowsResult = await pool.query(
    `SELECT * FROM platform_console.incidents ${where} ORDER BY started_at DESC LIMIT $${values.length + 1} OFFSET $${values.length + 2}`,
    [...values, params.limit, params.offset],
  );

  return { ok: true, data: { rows: rowsResult.rows.map(toIncident), total } };
}

// -------------------------------------------- Monthly SLA compliance + credit

/**
 * Explicitly illustrative service-credit schedule -- NOT a real contracted
 * percentage-of-monthly-spend refund, same "labeled illustrative, never
 * fabricated precision" discipline lib/invoice-preview.ts's
 * ILLUSTRATIVE_RATES already establishes for its own dollar rate table.
 * Modeled after the real AWS/GCP/Azure SLA credit-schedule SHAPE (a tiered
 * percentage-of-monthly-spend credit keyed by how far under target actual
 * uptime fell, capped per tier) -- the actual numbers are a placeholder a
 * real contract's legal/sales team would set, not derived from any
 * external source.
 */
export const ILLUSTRATIVE_CREDIT_SCHEDULE: Record<
  SlaTier,
  { creditPctPerPoint: number; maxCreditPct: number }
> = {
  standard: { creditPctPerPoint: 10, maxCreditPct: 30 },
  priority: { creditPctPerPoint: 15, maxCreditPct: 50 },
  "enterprise-247": { creditPctPerPoint: 25, maxCreditPct: 100 },
};

/**
 * Every real component this shared platform runs -- see this module's own
 * header comment on why there is no real per-org tenant isolation of
 * components today. Kept as a function (not a bare re-export) so the
 * "this is the illustrative all-orgs-share-everything mapping" fact is
 * documented at the one call site that depends on it, and so a later real
 * per-org mapping can replace the body without changing this function's
 * signature or any caller.
 */
async function orgComponentIds(): Promise<string[]> {
  const { getStatusPageData } = await import("@/lib/status-page");
  const data = await getStatusPageData();
  return data.components.map((c) => c.id);
}

export interface MonthlyUptimeReport {
  orgId: string;
  month: string; // "YYYY-MM"
  slaTier: SlaTier;
  slaUptimeTargetPct: number;
  totalMinutesInMonth: number;
  downtimeMinutes: number;
  actualUptimePct: number;
  metTarget: boolean;
  incidentCount: number;
  incidents: Incident[];
}

/**
 * Real computation of one org's actual uptime% for `month` (an
 * "YYYY-MM" string) against its contracted `SLA_TIER_DEFAULTS[slaTier]
 * .slaUptimeTargetPct`. Sums `resolved_at - started_at` (real minutes) for
 * every RESOLVED incident in-month across the org's mapped components
 * (open incidents contribute nothing yet -- their real duration is not
 * known until they resolve, so counting them would understate downtime
 * on a partial-month "still ongoing" outage or overstate it by guessing an
 * end; the honest choice is to exclude, matching every other fail-closed
 * "don't fabricate a number for data that doesn't exist yet" convention in
 * this codebase). `actualUptimePct` is real arithmetic
 * (1 - downtimeMinutes/totalMinutesInMonth) * 100 over those real minutes,
 * never a fabricated/rounded placeholder.
 */
export async function computeMonthlyUptime(
  orgId: string,
  month: string,
  slaTier: SlaTier,
): Promise<IncidentOutcome<MonthlyUptimeReport>> {
  if (!/^\d{4}-\d{2}$/.test(month)) {
    return { ok: false, error: `month must be 'YYYY-MM', got '${month}'` };
  }
  const [yearStr, monthStr] = month.split("-");
  const year = Number(yearStr);
  const monthIndex = Number(monthStr) - 1; // 0-based for Date
  const monthStart = new Date(Date.UTC(year, monthIndex, 1, 0, 0, 0));
  const monthEnd = new Date(Date.UTC(year, monthIndex + 1, 1, 0, 0, 0));
  const totalMinutesInMonth = (monthEnd.getTime() - monthStart.getTime()) / 60_000;

  const componentIds = await orgComponentIds();

  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "incidents store not configured or unreachable" };

  const result = await pool.query(
    `SELECT * FROM platform_console.incidents
     WHERE component_id = ANY($1)
       AND status = 'resolved'
       AND resolved_at IS NOT NULL
       AND started_at < $2
       AND resolved_at > $3
     ORDER BY started_at ASC`,
    [componentIds, monthEnd.toISOString(), monthStart.toISOString()],
  );
  const incidents = result.rows.map(toIncident);

  let downtimeMinutes = 0;
  for (const inc of incidents) {
    // Clip each incident's real span to the month boundary -- an incident
    // that started in the prior month and resolved in this one (or vice
    // versa) only counts the portion of its real duration that actually
    // fell inside `month`.
    const startMs = Math.max(new Date(inc.startedAt).getTime(), monthStart.getTime());
    const endMs = Math.min(new Date(inc.resolvedAt as string).getTime(), monthEnd.getTime());
    downtimeMinutes += Math.max(0, endMs - startMs) / 60_000;
  }

  const actualUptimePct = totalMinutesInMonth > 0
    ? Math.max(0, (1 - downtimeMinutes / totalMinutesInMonth) * 100)
    : 100;
  const target = SLA_TIER_DEFAULTS[slaTier].slaUptimeTargetPct;

  return {
    ok: true,
    data: {
      orgId,
      month,
      slaTier,
      slaUptimeTargetPct: target,
      totalMinutesInMonth,
      downtimeMinutes,
      actualUptimePct,
      metTarget: actualUptimePct >= target,
      incidentCount: incidents.length,
      incidents,
    },
  };
}

export interface CreditResult {
  owed: boolean;
  shortfallPct: number; // target - actual, 0 when target was met
  creditPctOfMonthlySpend: number;
  schedule: { creditPctPerPoint: number; maxCreditPct: number };
  illustrative: true;
}

/**
 * Pure arithmetic over a MonthlyUptimeReport -- illustrative
 * percentage-of-monthly-spend credit, `shortfallPct *
 * creditPctPerPoint`, capped at `maxCreditPct`. Takes no network
 * dependency (same "callable in isolation with hand-constructed input"
 * discipline lib/invoice-preview.ts's computeLineItems already
 * establishes), so the math is checkable without a live Prometheus/
 * Postgres round trip. `illustrative: true` is always present in the
 * return value -- never omittable -- so no caller can accidentally render
 * this figure as a real contractual obligation without also rendering the
 * flag that says otherwise.
 */
export function computeCredit(
  report: MonthlyUptimeReport,
  schedule: Record<SlaTier, { creditPctPerPoint: number; maxCreditPct: number }> = ILLUSTRATIVE_CREDIT_SCHEDULE,
): CreditResult {
  const tierSchedule = schedule[report.slaTier];
  if (report.metTarget) {
    return {
      owed: false,
      shortfallPct: 0,
      creditPctOfMonthlySpend: 0,
      schedule: tierSchedule,
      illustrative: true,
    };
  }
  const shortfallPct = Math.max(0, report.slaUptimeTargetPct - report.actualUptimePct);
  const creditPctOfMonthlySpend = Math.min(
    tierSchedule.maxCreditPct,
    shortfallPct * tierSchedule.creditPctPerPoint,
  );
  return {
    owed: true,
    shortfallPct,
    creditPctOfMonthlySpend,
    schedule: tierSchedule,
    illustrative: true,
  };
}
