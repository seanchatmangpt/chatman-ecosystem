/**
 * Real, periodic Data-Residency Compliance Attestation -- the gap
 * docs/DATA-RESIDENCY.md's own scope note leaves open: region pinning
 * (lib/orgs.ts's `setOrgRegion`, `lib/k8s.ts`'s `REGION_NODE_LABEL`
 * nodeSelector injection) is enforced only at PROVISIONING time, and
 * `getOrgRegion` only ever answers "what region is this org pinned to
 * right now" -- neither one is a recurring, persisted proof that pinning
 * actually HELD over an audit period. A Fortune-5 compliance/legal team
 * (GDPR Art. 44-49 cross-border-transfer restrictions, sector-specific
 * data-sovereignty clauses) needs exactly that: a dated artifact an
 * external auditor can be handed, distinct from lib/compliance-report.ts
 * (SOC2/ISO27001-style continuous-monitoring report covering audit-log
 * volume, IP allowlist, cost anomalies, and admission-policy bindings --
 * never region-specific placement drift).
 *
 * DETECTION: `runResidencyAttestationScanForOrg` fabricates nothing --
 * for one org with a real pinned `region` (lib/orgs.ts), it lists that
 * org's real live Pods (lib/k8s.ts's `listPods`, each carrying its real,
 * scheduler-assigned `spec.nodeName`) and this cluster's real live Node
 * `topology.kubernetes.io/region` labels (`getNodeRegionLabels`, the same
 * well-known label `setOrgRegion`'s own live validation and
 * `buildProjectManifest`'s `nodeSelector` injection already trust), then
 * flags every Pod whose ACTUAL node's region label does not equal the
 * org's pinned region as a drift event. A Pod not yet scheduled
 * (`nodeName: null`) or scheduled onto an unlabeled node is ALSO drift --
 * absence of evidence is never treated as evidence of compliance.
 *
 * PERSISTENCE: one real `platform_console.residency_attestations`
 * Postgres row PER SCAN, appended (never UPSERTed, never UPDATEd) --
 * same demo-project Postgres pool (`lib/audit-db.ts`'s `getAuditDbPool`)
 * and `CREATE TABLE IF NOT EXISTS` self-bootstrap convention
 * lib/patch-sla.ts's `ensurePatchSlaTables` already establishes. Because
 * every scan writes a brand-new immutable row, a "clean history" claim
 * ("drift_count = 0 for every one of the last N periods") is provable
 * straight from the row count -- there is no mutable "current status"
 * field an operator (or an attacker) could quietly flip back to
 * compliant after a real drift was observed.
 *
 * SCHEDULING: `runResidencyAttestationScan` is the platform-wide walker
 * a scheduled job's unattended HTTP call runs -- same "GET reads, a
 * separate scan writes" division of labor, and the same "cron and
 * on-demand call the exact same function" discipline, as
 * lib/patch-sla.ts's `runPatchSlaBreachScan` / lib/compliance-report.ts's
 * `generateComplianceReport` already establish for their own recurring
 * artifacts.
 */
import type { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";
import { listPods, getNodeRegionLabels } from "@/lib/k8s";
import { listOrgs, getOrg, type Org } from "@/lib/orgs";

export type ResidencyAttestationOutcome<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

/** One real Pod whose actual node placement did not match the org's
 * pinned region at scan time. `actualRegion: null` covers both an
 * unscheduled Pod and a Pod scheduled onto a node with no region label
 * -- both are real, honestly-reported "cannot prove compliance" states,
 * never coerced into a fabricated region string. */
export interface ResidencyDriftEvent {
  podName: string;
  nodeName: string | null;
  actualRegion: string | null;
  expectedRegion: string;
}

/** One real, immutable attestation row -- the unit `platform_console.
 * residency_attestations` persists, one per (org, scan). */
export interface ResidencyAttestation {
  id: string;
  orgId: string;
  namespace: string;
  region: string;
  /** RFC3339 timestamp this scan's observation was taken -- the period
   * this row attests to. */
  period: string;
  workloadsChecked: number;
  driftCount: number;
  driftEvents: ResidencyDriftEvent[];
  attestedAt: string;
}

async function ensureResidencyAttestationsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`).catch(() => {});
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.residency_attestations (
      id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      org_id            text NOT NULL,
      namespace         text NOT NULL,
      region            text NOT NULL,
      period            timestamptz NOT NULL,
      workloads_checked integer NOT NULL,
      drift_count       integer NOT NULL,
      drift_events      jsonb NOT NULL,
      attested_at       timestamptz NOT NULL DEFAULT now()
    )
  `);
  // No UNIQUE constraint on (org_id, period) -- append-only by design (see
  // this module's header comment): every real scan gets its own row, so
  // a clean-history claim is provable from COUNT(*)/SUM(drift_count),
  // never from a row that could have been overwritten in place.
  await pool.query(
    `CREATE INDEX IF NOT EXISTS residency_attestations_org_idx
       ON platform_console.residency_attestations (org_id, period DESC)`,
  );
}

let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureResidencyAttestationsTable(pool);
  }
  await tableReady;
  return pool;
}

function toAttestation(r: Record<string, unknown>): ResidencyAttestation {
  return {
    id: r.id as string,
    orgId: r.org_id as string,
    namespace: r.namespace as string,
    region: r.region as string,
    period: new Date(r.period as string).toISOString(),
    workloadsChecked: r.workloads_checked as number,
    driftCount: r.drift_count as number,
    driftEvents: (r.drift_events ?? []) as ResidencyDriftEvent[],
    attestedAt: new Date(r.attested_at as string).toISOString(),
  };
}

/**
 * Real, read-only drift computation for one org already known to have a
 * pinned `region` -- lists its real live Pods and checks each one's real
 * `nodeName` against the live `nodeRegions` map. Performs no writes; the
 * caller decides whether/how to persist the result.
 */
async function computeOrgDrift(
  org: Org,
  nodeRegions: Record<string, string | undefined>,
): Promise<{ workloadsChecked: number; driftEvents: ResidencyDriftEvent[]; error: string | null }> {
  const podsResult = await listPods(org.namespace);
  if (!podsResult.ok) {
    return { workloadsChecked: 0, driftEvents: [], error: podsResult.error };
  }
  const region = org.region as string;
  const driftEvents: ResidencyDriftEvent[] = [];
  for (const pod of podsResult.data) {
    const actualRegion = pod.nodeName ? nodeRegions[pod.nodeName] ?? null : null;
    if (actualRegion !== region) {
      driftEvents.push({
        podName: pod.name,
        nodeName: pod.nodeName,
        actualRegion,
        expectedRegion: region,
      });
    }
  }
  return { workloadsChecked: podsResult.data.length, driftEvents, error: null };
}

async function persistAttestation(
  pool: Pool,
  org: Org,
  scan: { workloadsChecked: number; driftEvents: ResidencyDriftEvent[] },
): Promise<ResidencyAttestation> {
  const result = await pool.query(
    `INSERT INTO platform_console.residency_attestations
       (org_id, namespace, region, period, workloads_checked, drift_count, drift_events)
     VALUES ($1, $2, $3, now(), $4, $5, $6::jsonb)
     RETURNING *`,
    [
      org.id,
      org.namespace,
      org.region,
      scan.workloadsChecked,
      scan.driftEvents.length,
      JSON.stringify(scan.driftEvents),
    ],
  );
  return toAttestation(result.rows[0] as Record<string, unknown>);
}

/**
 * Real, single-org attestation: scans this org's real live placement
 * against its pinned region and appends one real immutable row. Used
 * both by the per-org on-demand/cron POST route and, per-org, by the
 * platform-wide walker below -- the exact same code path either way, so
 * a cadence-triggered attestation and an on-demand one are never two
 * divergent implementations.
 */
export async function runResidencyAttestationScanForOrg(
  orgId: string,
): Promise<ResidencyAttestationOutcome<ResidencyAttestation>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "residency attestation store not configured or unreachable" };
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) return { ok: false, error: orgResult.error };
  if (!orgResult.data) return { ok: false, error: `org '${orgId}' not found` };
  const org = orgResult.data;
  if (!org.region) {
    return { ok: false, error: `org '${orgId}' has no pinned region -- nothing to attest` };
  }

  const nodeRegionsResult = await getNodeRegionLabels();
  if (!nodeRegionsResult.ok) return nodeRegionsResult;

  const scan = await computeOrgDrift(org, nodeRegionsResult.data);
  if (scan.error) return { ok: false, error: scan.error };

  const attestation = await persistAttestation(pool, org, scan);
  return { ok: true, data: attestation };
}

export interface ResidencyAttestationScanReport {
  scannedAt: string;
  orgsScanned: number;
  orgsSkipped: number; // no pinned region
  results: Array<{
    orgId: string;
    region: string | null;
    workloadsChecked: number;
    driftCount: number;
    error: string | null;
  }>;
}

/**
 * The real, unattended, platform-wide entry point a scheduled job's HTTP
 * call runs: walks every org with a pinned `region` (lib/orgs.ts's
 * `listOrgs`) and attests each one via `runResidencyAttestationScanForOrg`
 * above. One org's k8s read failing (recorded on that org's own result)
 * never aborts the whole walk -- same "one org's failure never blocks
 * every other org" discipline lib/patch-sla.ts's `runPatchSlaBreachScan`
 * already establishes.
 */
export async function runResidencyAttestationScan(): Promise<
  ResidencyAttestationOutcome<ResidencyAttestationScanReport>
> {
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) return { ok: false, error: orgsResult.error };

  const report: ResidencyAttestationScanReport = {
    scannedAt: new Date().toISOString(),
    orgsScanned: 0,
    orgsSkipped: 0,
    results: [],
  };

  for (const org of orgsResult.data) {
    if (!org.region) {
      report.orgsSkipped += 1;
      continue;
    }
    report.orgsScanned += 1;
    const scanResult = await runResidencyAttestationScanForOrg(org.id);
    if (!scanResult.ok) {
      report.results.push({
        orgId: org.id,
        region: org.region,
        workloadsChecked: 0,
        driftCount: 0,
        error: scanResult.error,
      });
      continue;
    }
    report.results.push({
      orgId: org.id,
      region: scanResult.data.region,
      workloadsChecked: scanResult.data.workloadsChecked,
      driftCount: scanResult.data.driftCount,
      error: null,
    });
  }

  return { ok: true, data: report };
}

/** Real, newest-first attestation history for one org -- backs
 * GET /api/orgs/[id]/residency-attestations and the compliance
 * dashboard/PDF export path lib/compliance-report.ts already
 * established for the broader SOC2/access-controls report. */
export async function listResidencyAttestations(
  orgId: string,
): Promise<ResidencyAttestationOutcome<ResidencyAttestation[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "residency attestation store not configured or unreachable" };
  }
  const result = await pool.query(
    `SELECT * FROM platform_console.residency_attestations WHERE org_id = $1 ORDER BY period DESC`,
    [orgId],
  );
  return { ok: true, data: result.rows.map((r) => toAttestation(r as Record<string, unknown>)) };
}
