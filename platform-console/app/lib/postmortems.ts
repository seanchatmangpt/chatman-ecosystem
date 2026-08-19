/**
 * Real Incident Postmortem / Root-Cause-Analysis document generator, tied
 * to the SLA-credit calculator (lib/incidents.ts's computeCredit /
 * computeMonthlyUptime, applied to Stripe via
 * lib/stripe-billing.ts's applySlaCreditToStripeBalance -- see
 * app/api/orgs/[id]/sla-credits/route.ts). Closes the gap that route's
 * own header comment implicitly leaves open: this repo already computes
 * a real severity, a real downtime duration, and a real illustrative
 * credit amount for every incident, but produces no written document --
 * Fortune 5 procurement/legal contracts commonly require a delivered
 * postmortem (timeline, impact, root cause, remediation) within N days
 * of any SLA-breaching incident, and today that is a manual doc an SRE
 * writes from scratch in some other tool this codebase has no record of.
 *
 * Storage: one real k8s ConfigMap (`platform-postmortems`,
 * `platform-console` namespace), reusing the exact
 * get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
 * established (`getConfigMap`/`createOrUpdateConfigMap`) -- the same
 * primitive lib/contract-renewals.ts and lib/budget-alerts.ts already
 * reuse for their own ConfigMaps. One `data` key per incident, keyed by
 * the incident's own `id` (lib/incidents.ts's Incident.id, the real
 * Postgres uuid primary key) -- never a second, independently-assigned
 * id for the same incident. The `platform-console-feature-flags` Role
 * (k8s/paas-rbac.yaml) already grants get/list/create/update/patch on
 * `configmaps` in this namespace with no `resourceNames` restriction, so
 * this ConfigMap is already covered with zero RBAC-manifest changes.
 *
 * Fact/judgment split, enforced structurally by this module's own
 * function signatures (never by caller discipline alone):
 *   - `generatePostmortem` auto-fills ONLY fields this repo already
 *     tracks as fact: the incident's real start/resolved timestamps (a
 *     `timeline` built from them), real `severity`, real
 *     `durationMinutes` (resolved_at - started_at), real `slaBreached`
 *     (actualUptimePct < SLA_TIER_DEFAULTS[org.slaTier]
 *     .slaUptimeTargetPct for the incident's month, via
 *     lib/incidents.ts's own computeMonthlyUptime/computeCredit -- the
 *     identical math app/api/orgs/[id]/sla-credits/route.ts's GET
 *     reports and POST applies to Stripe), and real `creditAmount`
 *     (`creditPctOfMonthlySpend`, illustrative -- see computeCredit's own
 *     doc comment). It takes NO rootCause/remediation parameter at all,
 *     so a caller cannot accidentally fabricate either into the initial
 *     draft.
 *   - `finalizePostmortem` is the ONLY function that ever writes
 *     `rootCause`/`remediation` -- always human-authored free text an
 *     SRE supplies via PATCH, never auto-generated, and it is the only
 *     function that can move `status` to `"final"` (requires both fields
 *     to be genuinely non-empty first -- a customer-facing "final"
 *     postmortem with an empty root cause would be worse than no
 *     document at all).
 *
 * Re-generating an existing incident's postmortem (a second POST) is a
 * real refresh of the FACTUAL fields only -- timeline/duration/severity/
 * credit are re-derived fresh from the incident/SLA data every time
 * (never trusted stale) -- but never overwrites an SRE's already-entered
 * `rootCause`/`remediation`/`status` once a draft exists, matching this
 * repo's "never silently clobber human-entered judgment with a re-run of
 * the automatic part" convention (see lib/incidents.ts's annotateIncident
 * doc comment on the same principle for `rootCause` there).
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getIncident, type Incident, type IncidentSeverity } from "@/lib/incidents";
import { computeMonthlyUptime, computeCredit } from "@/lib/incidents";
import { getOrgSla } from "@/lib/orgs";
import { SLA_TIER_DEFAULTS } from "@/lib/tiers";

export const POSTMORTEMS_NAMESPACE = "platform-console";
export const POSTMORTEMS_CONFIGMAP = "platform-postmortems";

export type PostmortemStatus = "draft" | "final";

export interface PostmortemTimelineEntry {
  /** RFC3339 -- either the incident's real startedAt/resolvedAt, or (for
   * `"observed"`) the moment this document was generated relative to
   * them. Never a fabricated intermediate timestamp this repo has no
   * record of. */
  at: string;
  event: string;
}

export interface PostmortemDoc {
  incidentId: string;
  orgId: string | null;
  componentId: string;
  timeline: PostmortemTimelineEntry[];
  severity: IncidentSeverity;
  durationMinutes: number;
  slaBreached: boolean;
  /** "YYYY-MM" -- the incident's resolution month, the same month
   * computeMonthlyUptime/computeCredit were evaluated against. Null while
   * the incident is still open (no resolvedAt yet -- see
   * generatePostmortem's fail-closed guard). */
  slaMonth: string | null;
  /** Illustrative percentage-of-monthly-spend credit for `slaMonth`, the
   * exact same computeCredit() figure app/api/orgs/[id]/sla-credits GET
   * reports and POST applies to Stripe -- never a second, independently
   * computed number. 0 when the org's target was met that month. */
  creditAmount: number;
  /** Always present, mirrors computeCredit's own `illustrative: true` --
   * this figure is a placeholder credit-schedule calculation, never a
   * real contractual dollar amount, until a real Stripe transaction (see
   * app/api/orgs/[id]/sla-credits POST) actually applies it. */
  creditIllustrative: true;
  /** Human-authored only -- see this module's header comment. Empty
   * string until an SRE PATCHes it in via finalizePostmortem. */
  rootCause: string;
  /** Human-authored only -- see this module's header comment. */
  remediation: string;
  status: PostmortemStatus;
  generatedAt: string; // RFC3339, set once by generatePostmortem, never rewritten
  generatedBy: string;
  updatedAt: string;
  updatedBy: string;
  finalizedAt: string | null;
  finalizedBy: string | null;
}

export type PostmortemOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

function isStatus(value: unknown): value is PostmortemStatus {
  return value === "draft" || value === "final";
}

function isTimeline(value: unknown): value is PostmortemTimelineEntry[] {
  return (
    Array.isArray(value) &&
    value.every(
      (e) =>
        e &&
        typeof e === "object" &&
        typeof (e as PostmortemTimelineEntry).at === "string" &&
        typeof (e as PostmortemTimelineEntry).event === "string",
    )
  );
}

function parsePostmortem(raw: string): PostmortemDoc | null {
  try {
    const p = JSON.parse(raw) as Partial<PostmortemDoc>;
    if (
      typeof p.incidentId === "string" &&
      (p.orgId === null || typeof p.orgId === "string") &&
      typeof p.componentId === "string" &&
      isTimeline(p.timeline) &&
      typeof p.severity === "string" &&
      typeof p.durationMinutes === "number" &&
      Number.isFinite(p.durationMinutes) &&
      (p.slaMonth === null || typeof p.slaMonth === "string") &&
      typeof p.slaBreached === "boolean" &&
      typeof p.creditAmount === "number" &&
      Number.isFinite(p.creditAmount) &&
      typeof p.rootCause === "string" &&
      typeof p.remediation === "string" &&
      isStatus(p.status) &&
      typeof p.generatedAt === "string" &&
      typeof p.generatedBy === "string" &&
      typeof p.updatedAt === "string" &&
      typeof p.updatedBy === "string" &&
      (p.finalizedAt === null || typeof p.finalizedAt === "string") &&
      (p.finalizedBy === null || typeof p.finalizedBy === "string")
    ) {
      return {
        incidentId: p.incidentId,
        orgId: p.orgId ?? null,
        componentId: p.componentId,
        timeline: p.timeline,
        severity: p.severity as IncidentSeverity,
        durationMinutes: p.durationMinutes,
        slaBreached: p.slaBreached,
        slaMonth: p.slaMonth ?? null,
        creditAmount: p.creditAmount,
        creditIllustrative: true,
        rootCause: p.rootCause,
        remediation: p.remediation,
        status: p.status,
        generatedAt: p.generatedAt,
        generatedBy: p.generatedBy,
        updatedAt: p.updatedAt,
        updatedBy: p.updatedBy,
        finalizedAt: p.finalizedAt ?? null,
        finalizedBy: p.finalizedBy ?? null,
      };
    }
    return null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, PostmortemDoc>>> {
  const cm = await getConfigMap(POSTMORTEMS_NAMESPACE, POSTMORTEMS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, PostmortemDoc>();
  for (const [incidentId, raw] of Object.entries(data)) {
    const parsed = parsePostmortem(raw);
    if (parsed) out.set(incidentId, parsed);
  }
  return { ok: true, data: out };
}

/** GET /api/incidents/[id]/postmortem -- read-only fetch of whatever
 * draft/final doc already exists for this incident, or null if none has
 * been generated yet. */
export async function getPostmortem(incidentId: string): Promise<PostmortemOutcome<PostmortemDoc | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(incidentId) ?? null };
}

function monthOf(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

/**
 * Real draft generator -- backs POST /api/incidents/[id]/postmortem.
 * Reads the incident's own real record (lib/incidents.ts's getIncident),
 * fails closed with an honest error if the incident is still `open` (no
 * real resolvedAt/duration to report yet -- never fabricates a partial
 * timeline for an ongoing outage), builds the timeline from the two real
 * timestamps the reconciler itself wrote, and -- when the incident is
 * mapped to a real org -- re-runs the exact same computeMonthlyUptime/
 * computeCredit math app/api/orgs/[id]/sla-credits/route.ts's GET already
 * reports for that incident's resolution month, so `slaBreached` and
 * `creditAmount` are never a second, independently-derived figure.
 *
 * Re-generating an existing incident (a second call) refreshes only the
 * factual fields -- timeline/severity/durationMinutes/slaBreached/
 * creditAmount/slaMonth -- and leaves rootCause/remediation/status/
 * finalizedAt/finalizedBy exactly as an SRE already entered them, never
 * resetting a draft an SRE is already writing into.
 */
export async function generatePostmortem(
  incidentId: string,
  actor: string,
): Promise<PostmortemOutcome<PostmortemDoc>> {
  const incidentResult = await getIncident(incidentId);
  if (!incidentResult.ok) return { ok: false, error: incidentResult.error };
  const incident = incidentResult.data;
  if (!incident) return { ok: false, error: `incident '${incidentId}' not found` };
  if (incident.status !== "resolved" || !incident.resolvedAt) {
    return {
      ok: false,
      error:
        `incident '${incidentId}' is still open -- a postmortem requires a real resolved duration, ` +
        "cannot be generated until the incident's resolvedAt is known",
    };
  }

  const durationMinutes =
    (new Date(incident.resolvedAt).getTime() - new Date(incident.startedAt).getTime()) / 60_000;

  const timeline: PostmortemTimelineEntry[] = [
    { at: incident.startedAt, event: `Incident opened -- component '${incident.componentId}' detected down` },
    { at: incident.resolvedAt, event: `Incident resolved -- component '${incident.componentId}' back up` },
  ];

  let slaBreached = false;
  let slaMonth: string | null = null;
  let creditAmount = 0;

  if (incident.orgId) {
    const slaResult = await getOrgSla(incident.orgId);
    if (!slaResult.ok) return { ok: false, error: slaResult.error };
    if (slaResult.data) {
      const month = monthOf(incident.resolvedAt);
      const reportResult = await computeMonthlyUptime(incident.orgId, month, slaResult.data.slaTier);
      if (!reportResult.ok) return { ok: false, error: reportResult.error };
      const credit = computeCredit(reportResult.data);
      slaMonth = month;
      slaBreached = !reportResult.data.metTarget;
      creditAmount = credit.creditPctOfMonthlySpend;
      timeline.push({
        at: incident.resolvedAt,
        event: slaBreached
          ? `SLA breach confirmed for ${month}: actual uptime ${reportResult.data.actualUptimePct.toFixed(4)}% ` +
            `vs contracted target ${SLA_TIER_DEFAULTS[slaResult.data.slaTier].slaUptimeTargetPct}%`
          : `Org's contracted uptime target for ${month} was met despite this incident`,
      });
    }
  }

  const now = new Date().toISOString();
  const all = await readAll();
  if (!all.ok) return all;
  const existing = all.data.get(incidentId) ?? null;

  const doc: PostmortemDoc = existing
    ? {
        ...existing,
        componentId: incident.componentId,
        timeline,
        severity: incident.severity,
        durationMinutes,
        slaBreached,
        slaMonth,
        creditAmount,
        creditIllustrative: true,
        updatedAt: now,
        updatedBy: actor,
      }
    : {
        incidentId,
        orgId: incident.orgId,
        componentId: incident.componentId,
        timeline,
        severity: incident.severity,
        durationMinutes,
        slaBreached,
        slaMonth,
        creditAmount,
        creditIllustrative: true,
        rootCause: "",
        remediation: "",
        status: "draft",
        generatedAt: now,
        generatedBy: actor,
        updatedAt: now,
        updatedBy: actor,
        finalizedAt: null,
        finalizedBy: null,
      };

  const result = await createOrUpdateConfigMap(POSTMORTEMS_NAMESPACE, POSTMORTEMS_CONFIGMAP, {
    [incidentId]: JSON.stringify(doc),
  });
  if (!result.ok) return result;
  return { ok: true, data: doc };
}

export interface FinalizePostmortemInput {
  incidentId: string;
  rootCause?: string;
  remediation?: string;
  /** Only `"final"` is ever accepted here -- there is no supported path
   * back from `"final"` to `"draft"` through this function; a customer-
   * facing document that already shipped is corrected by a new PATCH's
   * text edits (still `"final"`), not by un-finalizing it. */
  markFinal?: boolean;
  actor: string;
}

/**
 * The ONLY function that ever writes `rootCause`/`remediation`/`status:
 * "final"`/`finalizedAt`/`finalizedBy` -- backs PATCH
 * /api/incidents/[id]/postmortem. Requires a draft to already exist
 * (generatePostmortem must have run first -- there is no path to create
 * a postmortem's factual fields from here). `markFinal: true` fails
 * closed with a real validation error unless BOTH rootCause and
 * remediation are non-empty (after this PATCH's own edit, or already on
 * file from a prior PATCH) -- a "final" document with a blank root cause
 * would misrepresent this as a completed compliance deliverable.
 */
export async function finalizePostmortem(
  input: FinalizePostmortemInput,
): Promise<PostmortemOutcome<PostmortemDoc>> {
  const all = await readAll();
  if (!all.ok) return all;
  const existing = all.data.get(input.incidentId);
  if (!existing) {
    return {
      ok: false,
      error: `no postmortem draft exists for incident '${input.incidentId}' -- POST /api/incidents/${input.incidentId}/postmortem to generate one first`,
    };
  }

  const rootCause = input.rootCause !== undefined ? input.rootCause.trim() : existing.rootCause;
  const remediation = input.remediation !== undefined ? input.remediation.trim() : existing.remediation;

  if (input.markFinal && (!rootCause || !remediation)) {
    return {
      ok: false,
      error: "cannot mark a postmortem final without a non-empty rootCause and remediation",
    };
  }

  const now = new Date().toISOString();
  const doc: PostmortemDoc = {
    ...existing,
    rootCause,
    remediation,
    status: input.markFinal ? "final" : existing.status,
    updatedAt: now,
    updatedBy: input.actor,
    finalizedAt: input.markFinal ? now : existing.finalizedAt,
    finalizedBy: input.markFinal ? input.actor : existing.finalizedBy,
  };

  const result = await createOrUpdateConfigMap(POSTMORTEMS_NAMESPACE, POSTMORTEMS_CONFIGMAP, {
    [input.incidentId]: JSON.stringify(doc),
  });
  if (!result.ok) return result;
  return { ok: true, data: doc };
}
