import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import {
  listResidencyAttestations,
  runResidencyAttestationScanForOrg,
} from "@/lib/data-residency-attestation";

// Real Scheduled Data-Residency Compliance Attestation endpoint
// (lib/data-residency-attestation.ts) -- GET returns this org's real,
// period-by-period attestation history (one immutable Postgres row per
// past scan) plus its current drift status, for the compliance
// dashboard/PDF export path lib/compliance-report.ts's own
// GET .../compliance-reports already established. POST runs a real
// attestation scan NOW, the exact same code path
// (`runResidencyAttestationScanForOrg`) an unattended scheduled job's
// HTTP call runs on cadence -- same "cron and on-demand call one
// function" discipline app/api/orgs/[id]/compliance-reports/route.ts's
// own header comment documents for that sibling module.
//
// Distinct from lib/compliance-report.ts's SOC2/ISO27001-style report
// (audit volume, IP allowlist, cost anomalies, admission-policy
// bindings): this is region-specific PLACEMENT DRIFT detection --
// whether every one of this org's real live Pods stayed scheduled on a
// node actually labeled with the org's own pinned region, for GDPR
// Art. 44-49 / sector data-sovereignty review.
//
// Auth model (mirrors app/api/orgs/[id]/compliance-reports/route.ts
// exactly):
//   - GET: any authenticated member of this org (viewer and up).
//   - POST (scan now): member and up -- OR the real unattended scheduled
//     job, authenticated not by session but by a real shared secret
//     (`x-residency-attestation-cron-secret` matching this pod's own
//     `process.env.RESIDENCY_ATTESTATION_CRON_SECRET`), checked BEFORE
//     the session cookie so the job's Pod (which carries no session) can
//     reach this route at all.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.RESIDENCY_ATTESTATION_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-residency-attestation-cron-secret");
  return presented === expected;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);
  const path = `/api/orgs/${id}/residency-attestations`;

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRoleIn(session, namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  if (!orgResult.data?.region) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 200,
      requestId,
    });
    return NextResponse.json({
      namespace,
      region: null,
      currentDriftCount: null,
      currentStorageDriftCount: null,
      cleanHistory: null,
      history: [],
      message: `org '${id}' has no pinned region -- no residency attestation applies`,
    });
  }

  const historyResult = await listResidencyAttestations(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: historyResult.ok ? 200 : 502,
    requestId,
  });
  if (!historyResult.ok) {
    return NextResponse.json({ error: historyResult.error }, { status: 502 });
  }

  const mostRecent = historyResult.data[0] ?? null;
  return NextResponse.json({
    namespace,
    region: orgResult.data.region,
    currentDriftCount: mostRecent ? mostRecent.driftCount : null,
    currentStorageDriftCount: mostRecent ? mostRecent.storageDriftCount : null,
    // Provable straight from this org's own real, append-only row
    // history -- true only when every single past attestation, not just
    // the most recent one, observed zero drift in EITHER dimension
    // (compute placement AND storage/PVC placement).
    cleanHistory:
      historyResult.data.length > 0 &&
      historyResult.data.every((a) => a.driftCount === 0 && a.storageDriftCount === 0),
    history: historyResult.data,
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const path = `/api/orgs/${id}/residency-attestations`;
  const cronAuthenticated = isCronAuthenticated(request);

  let actor: string;

  if (cronAuthenticated) {
    // Unattended scheduled-job firing -- no session exists.
    actor = "residency-attestation-cronjob";
  } else {
    const session = await requireSession(request);
    if (!session) {
      return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
    }
    actor = roleIdentifierFor(session);

    const orgResult = await getOrg(id);
    if (!orgResult.ok) {
      return NextResponse.json({ error: orgResult.error }, { status: 502 });
    }
    const namespace = orgResult.data ? orgResult.data.namespace : id;

    const access = await requireRoleIn(session, namespace, "member");
    if (!access.ok) {
      writeAuditLogEntry({
        orgId: id,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path,
        status: 403,
        requestId,
      });
      return access.response!;
    }
  }

  const result = await runResidencyAttestationScanForOrg(id);

  // Durable, awaited audit write: this POST persists a real, immutable
  // sovereignty-attestation row (compute AND storage placement) that an
  // external auditor may be handed -- same "the record that the attestation
  // was RUN survives even if the response never reaches the caller" bar
  // as this repo's other maker-checker/security-relevant mutations
  // (tier.downgrade, pricing.override, freeze.override), so this call is
  // awaited rather than fire-and-forget like the read-only GET path above.
  await writeAuditLogEntryAwaited({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path,
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ attestation: result.data }, { status: 201 });
}
