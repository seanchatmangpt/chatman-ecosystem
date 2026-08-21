/**
 * Real Break-Glass Emergency Access -- the SIG/CAIQ ("do you have a
 * documented, logged emergency-access process distinct from normal
 * change management, with mandatory post-hoc review?") and SOC2 CC6.1
 * control this repo could not answer yes to with ONLY ordinary RBAC
 * (lib/authz.ts) and the maker-checker workflow
 * (lib/approval-workflow.ts) in place: those two controls both assume
 * there is TIME to wait for a second human before acting. An active
 * customer incident often does not give platform on-call that time --
 * this module is the deliberately-narrow, always-logged escape hatch:
 * a bounded-TTL grant onto one customer org's own namespace that a
 * single on-call engineer can open immediately (bypassing the normal
 * maker-checker gate `requireApproval` would otherwise impose on
 * touching a customer's live resources), in exchange for two things
 * ordinary RBAC never requires:
 *   1. every grant, every real read taken under it, and every expiry is
 *      written to the SAME hash-chained `platform_console.audit_log`
 *      every other privileged action in this app already lands in
 *      (via `writeAuditLogEntryAwaited` -- awaited, not fire-and-forget,
 *      because a break-glass event is exactly the kind of durable
 *      compliance evidence lib/export-custody.ts's own "must actually be
 *      committed before we treat it as proof" discipline applies to);
 *   2. a MANDATORY post-hoc justification, filed after the fact by the
 *      same on-call engineer, that itself requires a second, distinct
 *      owner-role approver to countersign via the existing
 *      lib/approval-workflow.ts maker-checker gate
 *      (`"break-glass.justification-review"`) -- so the two-person
 *      integrity this repo's other high-risk actions get BEFORE they
 *      execute, break-glass gets AFTER, which is the entire point of a
 *      break-glass control: speed now, accountability immediately after.
 *
 * Storage: a dedicated `platform_console.break_glass_grants` table on
 * the same live demo-project Postgres lib/audit-db.ts's
 * `getAuditDbPool()` and lib/impersonation.ts's
 * `platform_console.impersonation_sessions` already treat as this
 * console's own operational store -- same single-flight, self-healing
 * pool, same `CREATE TABLE IF NOT EXISTS` self-bootstrap convention, and
 * (deliberately) the same lazy, read-time TTL-expiry discipline
 * lib/impersonation.ts already established: no background sweep: every
 * read path below auto-ends an expired-but-still-"active" row
 * (`endedReason: "expired"`) the moment it is next observed.
 *
 * Distinct from lib/impersonation.ts on purpose, not a duplicate of it:
 * impersonation is "an admin views/acts inside a customer's CONSOLE
 * session", already maker-checker-exempt by original design and gated
 * on platform-admin rank alone. Break-glass is narrower and higher-risk
 * in a different way -- it is a real, live, namespace-scoped K8S READ
 * grant (`readNamespaceStateUnderGrant` below, backed by the exact
 * `k8sRequest` primitive lib/k8s-fault-scan.ts's own
 * `collectClusterStateForOrg` uses, never fabricated data) explicitly
 * carved out from the maker-checker gate every other namespace-touching
 * action in this app is expected to go through -- so it earns its own
 * mandatory-justification-plus-second-approver control on the BACK end
 * to compensate for having none on the front end.
 */
import type { Pool } from "pg";
import { getAuditDbPool, newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { k8sRequest, type K8sResult } from "@/lib/k8s";

/** Bounded TTL for a break-glass grant -- deliberately much shorter than
 * lib/impersonation.ts's 30-minute IMPERSONATION_TTL_MS: an emergency
 * grant onto a CUSTOMER'S namespace is a narrower, higher-blast-radius
 * escape hatch than viewing this console's own UI as that org, so it
 * gets a tighter box (15 minutes) and must be explicitly re-requested
 * (a fresh grant, fresh audit row, fresh justification obligation) if
 * the incident runs longer -- never silently renewed. */
export const BREAK_GLASS_TTL_MS = 15 * 60 * 1000;

/** Deadline for filing the mandatory post-hoc justification after a
 * grant ends (manually or by expiry) -- same "trailing window"
 * discipline lib/approval-workflow.ts's APPROVAL_TTL_HOURS documents,
 * here bounding the OTHER side: how long an on-call engineer has to
 * explain what they did before `listOverdueJustifications` below flags
 * the grant as delinquent for a reviewer. */
export const JUSTIFICATION_DEADLINE_MS = 24 * 60 * 60 * 1000; // 24 hours

export type BreakGlassEndedReason = "manual" | "expired" | null;

export interface BreakGlassGrant {
  id: string;
  adminUserId: string;
  targetOrgId: string;
  namespace: string;
  incidentReason: string; // required at grant time -- why this is an emergency
  startedAt: string; // RFC3339
  expiresAt: string; // RFC3339 -- startedAt + BREAK_GLASS_TTL_MS
  endedAt: string | null;
  endedReason: BreakGlassEndedReason;
  justification: string | null; // mandatory post-hoc explanation, filed after the fact
  justifiedAt: string | null;
  justificationApprovalRequestId: string | null; // cross-reference into platform-console-approvals
}

export type BreakGlassOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

async function ensureBreakGlassTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.break_glass_grants (
      id                              text PRIMARY KEY,
      admin_user_id                   text NOT NULL,
      target_org_id                   text NOT NULL,
      namespace                       text NOT NULL,
      incident_reason                 text NOT NULL,
      started_at                      timestamptz NOT NULL DEFAULT now(),
      expires_at                      timestamptz NOT NULL,
      ended_at                        timestamptz,
      ended_reason                    text,
      justification                   text,
      justified_at                    timestamptz,
      justification_approval_request_id text
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS break_glass_grants_target_org_id_idx
       ON platform_console.break_glass_grants (target_org_id)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution
// cache convention as lib/impersonation.ts's tableReady.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureBreakGlassTable(pool);
  }
  await tableReady;
  return pool;
}

function toGrant(r: Record<string, unknown>): BreakGlassGrant {
  return {
    id: r.id as string,
    adminUserId: r.admin_user_id as string,
    targetOrgId: r.target_org_id as string,
    namespace: r.namespace as string,
    incidentReason: r.incident_reason as string,
    startedAt: new Date(r.started_at as string).toISOString(),
    expiresAt: new Date(r.expires_at as string).toISOString(),
    endedAt: r.ended_at ? new Date(r.ended_at as string).toISOString() : null,
    endedReason: (r.ended_reason as BreakGlassEndedReason) ?? null,
    justification: (r.justification as string | null) ?? null,
    justifiedAt: r.justified_at ? new Date(r.justified_at as string).toISOString() : null,
    justificationApprovalRequestId: (r.justification_approval_request_id as string | null) ?? null,
  };
}

const SELECT_COLUMNS =
  "id, admin_user_id, target_org_id, namespace, incident_reason, started_at, expires_at, " +
  "ended_at, ended_reason, justification, justified_at, justification_approval_request_id";

/**
 * Opens a real, bounded-TTL break-glass grant. Deliberately does NOT
 * call lib/approval-workflow.ts's `requireApproval` -- bypassing the
 * normal maker-checker wait is the entire reason this control exists;
 * see this module's header comment for the compensating back-end
 * control (mandatory justification + second-approver review) that
 * makes that bypass defensible. Awaited audit write: this event must be
 * durably committed before the caller's response, not fire-and-forget,
 * because a break-glass grant IS the compliance evidence.
 */
export async function openBreakGlassGrant(input: {
  adminUserId: string;
  targetOrgId: string;
  namespace: string;
  incidentReason: string;
}): Promise<BreakGlassOutcome<BreakGlassGrant>> {
  const trimmedReason = input.incidentReason.trim();
  if (!trimmedReason) {
    return { ok: false, error: "incidentReason is required to open a break-glass grant" };
  }
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }

  const id = globalThis.crypto.randomUUID();
  const startedAt = new Date();
  const expiresAt = new Date(startedAt.getTime() + BREAK_GLASS_TTL_MS);

  try {
    const result = await pool.query(
      `INSERT INTO platform_console.break_glass_grants
         (id, admin_user_id, target_org_id, namespace, incident_reason, started_at, expires_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING ${SELECT_COLUMNS}`,
      [
        id,
        input.adminUserId,
        input.targetOrgId,
        input.namespace,
        trimmedReason,
        startedAt.toISOString(),
        expiresAt.toISOString(),
      ],
    );
    const grant = toGrant(result.rows[0]);

    await writeAuditLogEntryAwaited({
      requestId: newRequestId(),
      timestamp: startedAt.toISOString(),
      actor: input.adminUserId,
      method: "BREAK_GLASS_OPEN",
      path: `/orgs/${input.targetOrgId}/namespaces/${input.namespace} (grant ${id}: ${trimmedReason})`,
      status: 200,
      orgId: input.targetOrgId,
    });

    return { ok: true, data: grant };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Applies lazy TTL expiry to one already-fetched row -- same discipline
 * as lib/impersonation.ts's `applyLazyExpiry`: an "active" (ended_at IS
 * NULL) row whose expires_at has passed is ended right now with
 * endedReason "expired", written through the same awaited audit path as
 * a manual end, so auto-expiry is exactly as visible to a reviewer as
 * an explicit close.
 */
async function applyLazyExpiry(pool: Pool, grant: BreakGlassGrant): Promise<BreakGlassGrant> {
  if (grant.endedAt) return grant;
  if (new Date(grant.expiresAt).getTime() > Date.now()) return grant;

  const endedAt = new Date();
  const result = await pool.query(
    `UPDATE platform_console.break_glass_grants
     SET ended_at = $2, ended_reason = 'expired'
     WHERE id = $1 AND ended_at IS NULL
     RETURNING ${SELECT_COLUMNS}`,
    [grant.id, endedAt.toISOString()],
  );
  if (result.rowCount === 0) {
    // Lost a race with a concurrent manual close -- ended either way.
    return { ...grant, endedAt: endedAt.toISOString(), endedReason: "expired" };
  }
  const ended = toGrant(result.rows[0]);
  await writeAuditLogEntryAwaited({
    requestId: newRequestId(),
    timestamp: endedAt.toISOString(),
    actor: grant.adminUserId,
    method: "BREAK_GLASS_EXPIRE",
    path: `/orgs/${grant.targetOrgId}/namespaces/${grant.namespace} (grant ${grant.id}, auto-expired after ${BREAK_GLASS_TTL_MS / 60_000}m)`,
    status: 200,
    orgId: grant.targetOrgId,
  });
  return ended;
}

/** Real single-grant read with lazy TTL auto-expiry applied. */
export async function getBreakGlassGrant(
  id: string,
): Promise<BreakGlassOutcome<BreakGlassGrant | null>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants WHERE id = $1`,
      [id],
    );
    if (result.rowCount === 0) return { ok: true, data: null };
    const grant = await applyLazyExpiry(pool, toGrant(result.rows[0]));
    return { ok: true, data: grant };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Ends a break-glass grant early -- only the on-call engineer who
 * opened it may close it, same "can't touch someone else's record"
 * discipline lib/impersonation.ts's `endImpersonation` applies.
 */
export async function closeBreakGlassGrant(
  id: string,
  closedBy: string,
): Promise<BreakGlassOutcome<BreakGlassGrant>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  const existingResult = await pool.query(
    `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants WHERE id = $1`,
    [id],
  );
  if (existingResult.rowCount === 0) {
    return { ok: false, error: "break-glass grant not found" };
  }
  const current = await applyLazyExpiry(pool, toGrant(existingResult.rows[0]));
  if (current.endedAt) {
    return { ok: false, error: `break-glass grant is already ended (${current.endedReason})` };
  }
  if (current.adminUserId !== closedBy) {
    return { ok: false, error: "only the on-call engineer who opened this grant may close it" };
  }

  const endedAt = new Date();
  const result = await pool.query(
    `UPDATE platform_console.break_glass_grants
     SET ended_at = $2, ended_reason = 'manual'
     WHERE id = $1 AND ended_at IS NULL
     RETURNING ${SELECT_COLUMNS}`,
    [id, endedAt.toISOString()],
  );
  if (result.rowCount === 0) {
    return { ok: false, error: "break-glass grant is already ended" };
  }
  const ended = toGrant(result.rows[0]);
  await writeAuditLogEntryAwaited({
    requestId: newRequestId(),
    timestamp: endedAt.toISOString(),
    actor: closedBy,
    method: "BREAK_GLASS_CLOSE",
    path: `/orgs/${ended.targetOrgId}/namespaces/${ended.namespace} (grant ${id}, closed manually)`,
    status: 200,
    orgId: ended.targetOrgId,
  });
  return { ok: true, data: ended };
}

/**
 * Real per-request-path lookup: the currently active (not ended, not
 * yet expired) break-glass grant held BY this admin FOR this specific
 * org, if any -- the exact check `requireActiveBreakGlassGrant` below
 * needs before allowing a real namespace read to proceed. Same lazy TTL
 * auto-expiry discipline as every other read here.
 */
export async function getActiveBreakGlassGrantForAdmin(
  adminUserId: string,
  targetOrgId: string,
): Promise<BreakGlassOutcome<BreakGlassGrant | null>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants
       WHERE admin_user_id = $1 AND target_org_id = $2 AND ended_at IS NULL
       ORDER BY started_at DESC
       LIMIT 1`,
      [adminUserId, targetOrgId],
    );
    if (result.rowCount === 0) return { ok: true, data: null };
    const grant = await applyLazyExpiry(pool, toGrant(result.rows[0]));
    if (grant.endedAt) return { ok: true, data: null }; // lazily expired just now
    return { ok: true, data: grant };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * The real enforcement primitive a break-glass-gated route calls before
 * touching cluster state: returns the active grant or a real, specific
 * error string a route turns into a 403 -- never a silent fabricated
 * "allowed".
 */
export async function requireActiveBreakGlassGrant(
  adminUserId: string,
  targetOrgId: string,
): Promise<{ ok: true; grant: BreakGlassGrant } | { ok: false; error: string }> {
  const result = await getActiveBreakGlassGrantForAdmin(adminUserId, targetOrgId);
  if (!result.ok) return { ok: false, error: result.error };
  if (!result.data) {
    return {
      ok: false,
      error: "no active break-glass grant for this admin on this org -- open one first",
    };
  }
  return { ok: true, grant: result.data };
}

/**
 * Real customer-facing read: every break-glass grant that has ever
 * touched one org, most recent first -- backs GET
 * /api/orgs/[id]/break-glass-log, same shape as lib/impersonation.ts's
 * `listImpersonationSessionsForOrg`. Includes ended AND still-active
 * grants, each with lazy TTL expiry applied before it's returned.
 */
export async function listBreakGlassGrantsForOrg(
  targetOrgId: string,
): Promise<BreakGlassOutcome<BreakGlassGrant[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants
       WHERE target_org_id = $1
       ORDER BY started_at DESC`,
      [targetOrgId],
    );
    const grants = await Promise.all(result.rows.map((row) => applyLazyExpiry(pool, toGrant(row))));
    return { ok: true, data: grants };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Real, platform-wide compliance read: every grant that has ENDED
 * (manually or by expiry) more than JUSTIFICATION_DEADLINE_MS ago with
 * still no `justification` on file -- the exact "did every emergency
 * access get explained" list a SIG/CAIQ reviewer or an internal auditor
 * asks for. A grant that is filed here and never justified is a real,
 * durable finding, not a soft nudge -- nothing in this module auto-files
 * a justification on the engineer's behalf.
 */
export async function listOverdueJustifications(): Promise<BreakGlassOutcome<BreakGlassGrant[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  try {
    const cutoff = new Date(Date.now() - JUSTIFICATION_DEADLINE_MS);
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants
       WHERE ended_at IS NOT NULL AND ended_at < $1 AND justification IS NULL
       ORDER BY ended_at ASC`,
      [cutoff.toISOString()],
    );
    return { ok: true, data: result.rows.map(toGrant) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Files the mandatory post-hoc justification and, in the SAME call,
 * opens the second-approver review that closes the compensating-control
 * loop this module's header comment describes -- via
 * lib/approval-workflow.ts's `requireApproval` against the
 * `"break-glass.justification-review"` action (targetId: the grant's
 * own id). Only the on-call engineer who opened the grant may file its
 * justification (same identity discipline as `closeBreakGlassGrant`),
 * and only once a grant has actually ended -- filing a justification
 * for an action still in progress would let the engineer pre-author the
 * story before the incident is even over, which defeats the point of a
 * POST-hoc review.
 */
export async function fileBreakGlassJustification(input: {
  grantId: string;
  filedBy: string;
  justification: string;
}): Promise<BreakGlassOutcome<{ grant: BreakGlassGrant; approvalRequestId: string }>> {
  const trimmed = input.justification.trim();
  if (!trimmed) {
    return { ok: false, error: "justification text is required" };
  }
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "break-glass grant store not configured or unreachable" };
  }
  const existingResult = await pool.query(
    `SELECT ${SELECT_COLUMNS} FROM platform_console.break_glass_grants WHERE id = $1`,
    [input.grantId],
  );
  if (existingResult.rowCount === 0) {
    return { ok: false, error: "break-glass grant not found" };
  }
  const current = await applyLazyExpiry(pool, toGrant(existingResult.rows[0]));
  if (!current.endedAt) {
    return { ok: false, error: "cannot justify a grant that has not ended yet" };
  }
  if (current.adminUserId !== input.filedBy) {
    return { ok: false, error: "only the on-call engineer who opened this grant may justify it" };
  }
  if (current.justification) {
    return { ok: false, error: "this grant already has a justification on file" };
  }

  // Import kept local to avoid a module-load-order cycle: approval-workflow.ts
  // does not import lib/break-glass.ts, so this is a plain one-directional
  // dependency, same shape every other approval-gated route's own import
  // of lib/approval-workflow.ts already has.
  const { requireApproval } = await import("@/lib/approval-workflow");
  const approval = await requireApproval({
    action: "break-glass.justification-review",
    targetId: input.grantId,
    requestedBy: input.filedBy,
    resourcePayload: {
      requestedBreakGlassJustification: {
        targetOrgId: current.targetOrgId,
        namespace: current.namespace,
        incidentReason: current.incidentReason,
        justification: trimmed,
        grantStartedAt: current.startedAt,
        grantEndedAt: current.endedAt,
      },
    },
  });
  let approvalRequestId: string;
  if (approval.ok) {
    approvalRequestId = approval.approval.requestId;
  } else if ("request" in approval) {
    approvalRequestId = approval.request.requestId;
  } else {
    return { ok: false, error: approval.error };
  }

  const justifiedAt = new Date();
  const result = await pool.query(
    `UPDATE platform_console.break_glass_grants
     SET justification = $2, justified_at = $3, justification_approval_request_id = $4
     WHERE id = $1
     RETURNING ${SELECT_COLUMNS}`,
    [input.grantId, trimmed, justifiedAt.toISOString(), approvalRequestId],
  );
  const updated = toGrant(result.rows[0]);

  await writeAuditLogEntryAwaited({
    requestId: newRequestId(),
    timestamp: justifiedAt.toISOString(),
    actor: input.filedBy,
    method: "BREAK_GLASS_JUSTIFY",
    path: `/orgs/${updated.targetOrgId}/namespaces/${updated.namespace} (grant ${updated.id}, review ${approvalRequestId})`,
    status: 200,
    orgId: updated.targetOrgId,
  });

  return { ok: true, data: { grant: updated, approvalRequestId } };
}

/**
 * Real namespace-scoped Pod + Deployment read, gated on
 * `requireActiveBreakGlassGrant` by the caller -- the actual "touch a
 * customer's namespace" action this whole module exists to authorize
 * and log. Uses the exact same `k8sRequest` primitive
 * lib/k8s-fault-scan.ts's `collectClusterStateForOrg` already uses
 * against the real in-cluster API server; never fabricated data. Every
 * call is itself audit-logged (awaited) with the grant id attached, so
 * an org's `/api/orgs/[id]/break-glass-log?grantId=...` drill-down (same
 * pattern as lib/impersonation.ts's session-scoped query) has a real
 * trail of exactly what was read under the grant, not just that the
 * grant existed.
 */
export async function readNamespaceStateUnderGrant(
  grant: BreakGlassGrant,
): Promise<K8sResult<{ pods: unknown; deployments: unknown }>> {
  const [podsResult, deploymentsResult] = await Promise.all([
    k8sRequest<unknown>(`/api/v1/namespaces/${grant.namespace}/pods`),
    k8sRequest<unknown>(`/apis/apps/v1/namespaces/${grant.namespace}/deployments`),
  ]);

  const readAt = new Date().toISOString();
  await writeAuditLogEntryAwaited({
    requestId: newRequestId(),
    timestamp: readAt,
    actor: grant.adminUserId,
    method: "BREAK_GLASS_ACCESS",
    path: `/orgs/${grant.targetOrgId}/namespaces/${grant.namespace}/{pods,deployments} (grant ${grant.id})`,
    status: podsResult.ok && deploymentsResult.ok ? 200 : 502,
    orgId: grant.targetOrgId,
  });

  if (!podsResult.ok) return podsResult;
  if (!deploymentsResult.ok) return deploymentsResult;
  return { ok: true, data: { pods: podsResult.data, deployments: deploymentsResult.data } };
}
