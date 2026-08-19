/**
 * Real Contractual Patch-Timeliness SLA Tier (CVE Remediation Credits):
 * closes the gap this repo's own vuln-scan auto-remediation
 * (lib/security-scan-auto-remediate.ts's `Org.autoRemediateCritical`)
 * leaves open -- that control is a best-effort TECHNICAL control (files a
 * `deployment.quarantine` approval, never guaranteed to be approved or
 * to fire within any window). Fortune 5 security/procurement review
 * increasingly requires a written CONTRACTUAL patch-timeliness commitment
 * ("CRITICAL CVEs remediated within 24h") with financial credits on
 * breach -- a distinct axis from the existing uptime SLA
 * (lib/incidents.ts), scored against `Org.patchSlaTier`
 * (lib/orgs.ts) and `lib/tiers.ts`'s `PATCH_SLA_COMMITTED_HOURS` table.
 *
 * LIFECYCLE TRACKING: lib/vuln-scan.ts's `VulnScanRun` is ephemeral (read
 * live from a k8s Job's pods, then the Job is deleted) -- it has no
 * memory of when a finding first appeared. This module adds that memory:
 * a real `platform_console.patch_sla_findings` Postgres table (same
 * demo-project Postgres pool, `CREATE TABLE IF NOT EXISTS` self-bootstrap
 * convention lib/incidents.ts's `ensureIncidentsTable` already
 * establishes), keyed by (image_ref, vulnerability_id) -- one row per
 * distinct CVE-on-image, `detected_at` set the first time
 * `recordScanFindings` observes it in ANY finished scan run, `remediated
 * _at` set the first time a LATER finished run of the SAME image no
 * longer reports it (the honest, real signal that the fix actually
 * landed -- not merely that a `deployment.quarantine` approval was filed,
 * which only stops NEW traffic to a vulnerable Deployment and proves
 * nothing about the image itself being patched).
 *
 * BREACH DETECTION: `runPatchSlaBreachScan` walks every org with
 * `patchSlaTier` set (lib/orgs.ts's `listOrgs`), lists that org's real
 * live Deployments (lib/k8s.ts's `listDeployments`, same primitive
 * lib/security-scan-auto-remediate.ts already uses to bind a
 * platform-wide finding to a specific org's own namespace), and for every
 * container image that org actually runs, checks this module's own open
 * (`remediated_at IS NULL`) findings against
 * `PATCH_SLA_COMMITTED_HOURS[org.patchSlaTier][finding.severity]`. A
 * finding still open past its committed window is recorded (idempotently
 * -- `UNIQUE (org_id, image_ref, vulnerability_id)`, so re-running the
 * scan never double-records the same breach) into a second table,
 * `platform_console.patch_sla_breaches`.
 *
 * CREDIT APPLICATION: deliberately reuses lib/stripe-billing.ts's
 * `applySlaCreditToStripeBalance` AS-IS (same function the uptime SLA
 * credit pipeline, POST /api/orgs/[id]/sla-credits, already calls) --
 * this module only computes the illustrative credit percentage
 * (`computePatchSlaCredit`, same "illustrative: true, never fabricated
 * precision" discipline lib/incidents.ts's `computeCredit` establishes)
 * and marks which breach rows a real Stripe transaction was applied
 * against (`markBreachesCreditApplied`) -- the actual Stripe call, and
 * the org-level idempotency/maker-checker gating around it, is the exact
 * same code path the uptime SLA already exercises.
 */
import type { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";
import { listDeployments } from "@/lib/k8s";
import { listOrgs, type Org } from "@/lib/orgs";
import { PATCH_SLA_COMMITTED_HOURS, type PatchSlaTier } from "@/lib/tiers";
import type { VulnScanRun } from "@/lib/vuln-scan";

export type PatchSlaOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

// Only these two severities carry a contractual commitment -- see
// lib/tiers.ts's PATCH_SLA_COMMITTED_HOURS doc comment for why
// MEDIUM/LOW/UNKNOWN are real, tracked findings but never breach a
// patch-timeliness SLA.
export type CommittedSeverity = "CRITICAL" | "HIGH";

function isCommittedSeverity(value: string): value is CommittedSeverity {
  return value === "CRITICAL" || value === "HIGH";
}

export interface PatchSlaFinding {
  imageRef: string;
  vulnerabilityId: string;
  severity: CommittedSeverity;
  detectedAt: string; // RFC3339
  remediatedAt: string | null; // RFC3339, null while still open
}

async function ensurePatchSlaTables(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.patch_sla_findings (
      id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      image_ref        text NOT NULL,
      vulnerability_id text NOT NULL,
      severity         text NOT NULL,
      detected_at      timestamptz NOT NULL DEFAULT now(),
      remediated_at    timestamptz,
      created_at       timestamptz NOT NULL DEFAULT now(),
      updated_at       timestamptz NOT NULL DEFAULT now(),
      -- One row per real distinct CVE-on-image: a re-scan that observes
      -- the same (image, CVE) pair again must UPSERT onto the same row,
      -- never duplicate detectedAt.
      UNIQUE (image_ref, vulnerability_id)
    )
  `);
  await pool.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`).catch(() => {});
  await pool.query(
    `CREATE INDEX IF NOT EXISTS patch_sla_findings_open_idx ON platform_console.patch_sla_findings (image_ref) WHERE remediated_at IS NULL`,
  );
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.patch_sla_breaches (
      id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      org_id             text NOT NULL,
      image_ref          text NOT NULL,
      vulnerability_id   text NOT NULL,
      severity           text NOT NULL,
      patch_sla_tier     text NOT NULL,
      committed_hours    integer NOT NULL,
      detected_at        timestamptz NOT NULL,
      breached_at        timestamptz NOT NULL DEFAULT now(),
      credit_applied_at  timestamptz,
      -- Idempotent breach recording: the same org/image/CVE breach is
      -- recorded (and therefore credited) exactly once, no matter how
      -- many times the scan re-runs while the finding stays open.
      UNIQUE (org_id, image_ref, vulnerability_id)
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS patch_sla_breaches_org_idx ON platform_console.patch_sla_breaches (org_id, credit_applied_at)`,
  );
}

let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensurePatchSlaTables(pool);
  }
  await tableReady;
  return pool;
}

function toFinding(r: Record<string, unknown>): PatchSlaFinding {
  return {
    imageRef: r.image_ref as string,
    vulnerabilityId: r.vulnerability_id as string,
    severity: r.severity as CommittedSeverity,
    detectedAt: new Date(r.detected_at as string).toISOString(),
    remediatedAt: r.remediated_at ? new Date(r.remediated_at as string).toISOString() : null,
  };
}

export interface RecordScanFindingsSummary {
  newlyDetected: number;
  newlyRemediated: number;
  stillOpen: number;
}

/**
 * Real lifecycle write: called once per finished scan run (the same
 * "only sync a finished run's results" discipline lib/vuln-scan.ts's
 * `syncVulnDenylist` doc comment already establishes -- a still-running
 * Pending image makes no claim either way, so it must never silently
 * close out a real open finding it hasn't actually re-checked).
 *
 * For every image whose pod already finished (Succeeded or Failed) in
 * this run:
 *   1. Every CRITICAL/HIGH finding it reports is UPSERTed --
 *      `detected_at` is only ever set on first INSERT (never overwritten
 *      by `ON CONFLICT DO UPDATE`, so a later re-scan of the same open
 *      CVE keeps its real original detection time).
 *   2. Every PREVIOUSLY-OPEN row for that same image_ref that this run's
 *      finding list no longer reports is marked `remediated_at = now()`
 *      -- the honest "the fix actually landed, confirmed by a real
 *      re-scan" signal, never fabricated from an approval alone.
 */
export async function recordScanFindings(run: VulnScanRun): Promise<PatchSlaOutcome<RecordScanFindingsSummary>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };

  const summary: RecordScanFindingsSummary = { newlyDetected: 0, newlyRemediated: 0, stillOpen: 0 };

  for (const image of run.images) {
    const finished = image.phase === "Succeeded" || image.phase === "Failed";
    if (!finished) continue;
    // A pod that finished but produced no parsable output makes no real
    // claim about this image's findings either way -- never treat it as
    // "zero findings, everything remediated".
    if (image.error) continue;

    const currentIds = new Set<string>();
    for (const finding of image.findings) {
      if (!isCommittedSeverity(finding.severity)) continue;
      currentIds.add(finding.vulnerabilityId);

      const upsertResult = await pool.query(
        `INSERT INTO platform_console.patch_sla_findings
           (image_ref, vulnerability_id, severity, detected_at, remediated_at, updated_at)
         VALUES ($1, $2, $3, now(), NULL, now())
         ON CONFLICT (image_ref, vulnerability_id) DO UPDATE SET
           -- A CVE that re-appears after being marked remediated (a
           -- regression -- e.g. a rollback to a vulnerable image) is
           -- reopened with a fresh detected_at, same "real observed
           -- state wins" discipline as a re-opened incident.
           remediated_at = CASE
             WHEN platform_console.patch_sla_findings.remediated_at IS NOT NULL THEN NULL
             ELSE platform_console.patch_sla_findings.remediated_at
           END,
           detected_at = CASE
             WHEN platform_console.patch_sla_findings.remediated_at IS NOT NULL THEN now()
             ELSE platform_console.patch_sla_findings.detected_at
           END,
           severity = EXCLUDED.severity,
           updated_at = now()
         RETURNING (xmax = 0) AS inserted, (detected_at = updated_at) AS just_reopened_or_new`,
        [image.target.ref, finding.vulnerabilityId, finding.severity],
      );
      const row = upsertResult.rows[0] as { inserted: boolean } | undefined;
      if (row?.inserted) summary.newlyDetected += 1;
      else summary.stillOpen += 1;
    }

    // Close out every previously-open row for this image that this
    // finished, error-free run no longer reports.
    const closeResult = await pool.query(
      `UPDATE platform_console.patch_sla_findings
         SET remediated_at = now(), updated_at = now()
       WHERE image_ref = $1
         AND remediated_at IS NULL
         AND vulnerability_id <> ALL($2::text[])
       RETURNING id`,
      [image.target.ref, [...currentIds]],
    );
    summary.newlyRemediated += closeResult.rowCount ?? 0;
  }

  return { ok: true, data: summary };
}

/** Real read of every currently-open (`remediated_at IS NULL`) CRITICAL/
 * HIGH finding for a given image ref -- the input `runPatchSlaBreachScan`
 * scores against each org's actually-deployed images. */
export async function getOpenFindingsForImage(imageRef: string): Promise<PatchSlaOutcome<PatchSlaFinding[]>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };
  const result = await pool.query(
    `SELECT * FROM platform_console.patch_sla_findings
     WHERE image_ref = $1 AND remediated_at IS NULL
     ORDER BY detected_at ASC`,
    [imageRef],
  );
  return { ok: true, data: result.rows.map(toFinding) };
}

export interface PatchSlaBreach {
  orgId: string;
  imageRef: string;
  vulnerabilityId: string;
  severity: CommittedSeverity;
  patchSlaTier: PatchSlaTier;
  committedHours: number;
  detectedAt: string;
  hoursOverdue: number;
  breachedAt: string;
  creditAppliedAt: string | null;
}

function toBreach(r: Record<string, unknown>): PatchSlaBreach {
  const detectedAt = new Date(r.detected_at as string);
  const committedHours = r.committed_hours as number;
  const hoursOverdue = Math.max(
    0,
    (Date.now() - detectedAt.getTime()) / 3_600_000 - committedHours,
  );
  return {
    orgId: r.org_id as string,
    imageRef: r.image_ref as string,
    vulnerabilityId: r.vulnerability_id as string,
    severity: r.severity as CommittedSeverity,
    patchSlaTier: r.patch_sla_tier as PatchSlaTier,
    committedHours,
    detectedAt: detectedAt.toISOString(),
    hoursOverdue,
    breachedAt: new Date(r.breached_at as string).toISOString(),
    creditAppliedAt: r.credit_applied_at ? new Date(r.credit_applied_at as string).toISOString() : null,
  };
}

export interface OrgPatchSlaScanResult {
  orgId: string;
  patchSlaTier: PatchSlaTier;
  newBreaches: number;
  errors: string[];
}

export interface PatchSlaBreachScanReport {
  scannedAt: string;
  orgsScanned: number;
  orgsSkipped: number; // no patchSlaTier set
  results: OrgPatchSlaScanResult[];
}

/**
 * Real per-org breach walk: for one org already known to have a
 * `patchSlaTier`, lists its real live Deployments, and for every distinct
 * container image it actually runs, checks that image's real open
 * findings (`getOpenFindingsForImage`) against
 * `PATCH_SLA_COMMITTED_HOURS[org.patchSlaTier]`. A finding whose real
 * `detectedAt` is already older than the committed window is recorded
 * (idempotently, `ON CONFLICT DO NOTHING`) as a breach.
 */
async function scanOrgForBreaches(pool: Pool, org: Org): Promise<OrgPatchSlaScanResult> {
  const tier = org.patchSlaTier as PatchSlaTier;
  const result: OrgPatchSlaScanResult = { orgId: org.id, patchSlaTier: tier, newBreaches: 0, errors: [] };
  const committed = PATCH_SLA_COMMITTED_HOURS[tier];

  const deploymentsResult = await listDeployments(org.namespace);
  if (!deploymentsResult.ok) {
    result.errors.push(deploymentsResult.error);
    return result;
  }

  const imageRefs = new Set<string>();
  for (const deployment of deploymentsResult.data) {
    for (const container of deployment.containers) imageRefs.add(container.image);
  }

  for (const imageRef of imageRefs) {
    const findingsResult = await getOpenFindingsForImage(imageRef);
    if (!findingsResult.ok) {
      result.errors.push(findingsResult.error);
      continue;
    }

    for (const finding of findingsResult.data) {
      const committedHours = committed[finding.severity];
      const hoursSinceDetected = (Date.now() - new Date(finding.detectedAt).getTime()) / 3_600_000;
      if (hoursSinceDetected <= committedHours) continue;

      const insertResult = await pool.query(
        `INSERT INTO platform_console.patch_sla_breaches
           (org_id, image_ref, vulnerability_id, severity, patch_sla_tier, committed_hours, detected_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7)
         ON CONFLICT (org_id, image_ref, vulnerability_id) DO NOTHING
         RETURNING id`,
        [org.id, imageRef, finding.vulnerabilityId, finding.severity, tier, committedHours, finding.detectedAt],
      );
      if ((insertResult.rowCount ?? 0) > 0) result.newBreaches += 1;
    }
  }

  return result;
}

/**
 * The real, unattended entry point a `app/api/cron/`-convention route
 * calls on a schedule: walks every org with `patchSlaTier` set
 * (lib/orgs.ts's `listOrgs`, filtered), scores each against its real open
 * findings, and idempotently records any new breach. One org's k8s read
 * failing is recorded on that org's own result and never aborts the
 * whole walk -- same "one org's failure never blocks every other org"
 * discipline lib/security-scan-auto-remediate.ts's `autoRemediateCriticalFindings`
 * already establishes.
 */
export async function runPatchSlaBreachScan(): Promise<PatchSlaOutcome<PatchSlaBreachScanReport>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) return { ok: false, error: orgsResult.error };

  const report: PatchSlaBreachScanReport = {
    scannedAt: new Date().toISOString(),
    orgsScanned: 0,
    orgsSkipped: 0,
    results: [],
  };

  for (const org of orgsResult.data) {
    if (!org.patchSlaTier) {
      report.orgsSkipped += 1;
      continue;
    }
    report.orgsScanned += 1;
    report.results.push(await scanOrgForBreaches(pool, org));
  }

  return { ok: true, data: report };
}

/** Real read of one org's current breach rows -- backs both the cron
 * report's per-org detail and GET /api/orgs/[id]/patch-sla-credits. */
export async function getOrgPatchSlaBreaches(orgId: string): Promise<PatchSlaOutcome<PatchSlaBreach[]>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };
  const result = await pool.query(
    `SELECT * FROM platform_console.patch_sla_breaches WHERE org_id = $1 ORDER BY breached_at DESC`,
    [orgId],
  );
  return { ok: true, data: result.rows.map(toBreach) };
}

/** Real read of every currently open (never-credited) breach, platform-
 * wide -- backs GET /api/patch-sla/breaches, the admin visibility route. */
export async function listOpenPatchSlaBreaches(): Promise<PatchSlaOutcome<PatchSlaBreach[]>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };
  const result = await pool.query(
    `SELECT * FROM platform_console.patch_sla_breaches WHERE credit_applied_at IS NULL ORDER BY breached_at DESC`,
  );
  return { ok: true, data: result.rows.map(toBreach) };
}

// Explicitly illustrative service-credit schedule for patch-timeliness
// breaches -- same "labeled illustrative, never fabricated precision"
// discipline lib/incidents.ts's ILLUSTRATIVE_CREDIT_SCHEDULE already
// establishes for the uptime SLA. Keyed by tier (a higher committed tier
// carries a steeper per-breach credit, matching that a CRITICAL CVE
// sitting unpatched past a 4-hour enterprise-247 commitment is a more
// serious contractual miss than the same overrun against a 24-hour
// standard commitment), a flat percentage-of-monthly-spend per open,
// uncredited breach, capped per tier.
export const PATCH_SLA_ILLUSTRATIVE_CREDIT_SCHEDULE: Record<
  PatchSlaTier,
  { creditPctPerBreach: number; maxCreditPct: number }
> = {
  standard: { creditPctPerBreach: 5, maxCreditPct: 25 },
  priority: { creditPctPerBreach: 8, maxCreditPct: 40 },
  "enterprise-247": { creditPctPerBreach: 15, maxCreditPct: 75 },
};

export interface PatchSlaCreditResult {
  owed: boolean;
  breachCount: number;
  creditPctOfMonthlySpend: number;
  schedule: { creditPctPerBreach: number; maxCreditPct: number };
  illustrative: true;
}

/**
 * Pure arithmetic over a set of not-yet-credited breach rows -- same
 * "callable in isolation with hand-constructed input, `illustrative: true`
 * always present" discipline lib/incidents.ts's `computeCredit`
 * establishes for the uptime SLA's own credit math. The resulting
 * `creditPctOfMonthlySpend` is passed AS-IS into
 * lib/stripe-billing.ts's `applySlaCreditToStripeBalance` -- the exact
 * same Stripe-application function/parameter shape the uptime SLA credit
 * route already calls, reused wholesale per this capability's own scope.
 */
export function computePatchSlaCredit(
  breaches: PatchSlaBreach[],
  tier: PatchSlaTier,
  schedule: Record<PatchSlaTier, { creditPctPerBreach: number; maxCreditPct: number }> = PATCH_SLA_ILLUSTRATIVE_CREDIT_SCHEDULE,
): PatchSlaCreditResult {
  const tierSchedule = schedule[tier];
  const uncredited = breaches.filter((b) => b.creditAppliedAt === null);
  if (uncredited.length === 0) {
    return { owed: false, breachCount: 0, creditPctOfMonthlySpend: 0, schedule: tierSchedule, illustrative: true };
  }
  const creditPctOfMonthlySpend = Math.min(
    tierSchedule.maxCreditPct,
    uncredited.length * tierSchedule.creditPctPerBreach,
  );
  return {
    owed: true,
    breachCount: uncredited.length,
    creditPctOfMonthlySpend,
    schedule: tierSchedule,
    illustrative: true,
  };
}

/** Real write: marks every given breach row's `credit_applied_at` --
 * called ONLY after a real Stripe customer-balance transaction has
 * actually been created (same "record after the real side effect landed"
 * ordering discipline lib/orgs.ts's `setOrgLastSlaCreditAppliedMonth`
 * doc comment already establishes for the uptime SLA credit route). */
export async function markBreachesCreditApplied(breachOrgId: string): Promise<PatchSlaOutcome<number>> {
  const pool = await resolveReadyPool();
  if (!pool) return { ok: false, error: "patch-sla store not configured or unreachable" };
  const result = await pool.query(
    `UPDATE platform_console.patch_sla_breaches
       SET credit_applied_at = now()
     WHERE org_id = $1 AND credit_applied_at IS NULL
     RETURNING id`,
    [breachOrgId],
  );
  return { ok: true, data: result.rowCount ?? 0 };
}
