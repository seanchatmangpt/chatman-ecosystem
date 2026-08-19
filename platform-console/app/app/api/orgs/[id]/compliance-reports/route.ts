import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  generateComplianceReport,
  getComplianceCadence,
  listComplianceReports,
  periodForCadence,
  setComplianceCadence,
  CADENCE_CRON_SCHEDULE,
  type ComplianceCadenceInterval,
} from "@/lib/compliance-report";

// Real Scheduled Compliance Report collection endpoint (lib/compliance-
// report.ts) -- GET lists every previously-generated report for one org
// plus its currently-set cadence; POST generates a new report NOW, the
// exact same code path (`generateComplianceReport`) lib/scheduled-
// jobs.ts's `createComplianceReportCronJob` curls unattended on the
// operator-set cadence, so an auditor comparing a cadence-triggered
// report against an on-demand one is comparing two runs of one function,
// never two divergent implementations. PUT sets the recurring cadence
// (owner-only) that determines both the CronJob schedule an operator
// applies via /scheduled-jobs-style tooling and the period POST computes
// when no explicit period is given.
//
// `id` resolution follows the exact same convention every other
// `/api/orgs/[id]/*` route in this tree already uses (see
// app/api/orgs/[id]/ip-allowlist/route.ts's own header comment): resolve
// against the real `platform-console-orgs` registry first; when `id`
// doesn't resolve there, `id` is used directly as both the org id AND
// the k8s namespace -- this deployment's one real single-tenant case
// (`platform-console`).
//
// Auth model:
//   - GET: any authenticated member of this org (viewer and up) --
//     reading past reports is not itself a privileged action, same
//     posture as branding's GET.
//   - POST (generate): member and up -- generating a report only reads
//     other modules' already-exposed data and writes a new, additive
//     ConfigMap key; OR the real unattended CronJob path, authenticated
//     not by session but by a real shared secret
//     (`x-compliance-cron-secret` matching this pod's own
//     `process.env.COMPLIANCE_CRON_SECRET`) -- see lib/scheduled-jobs.ts's
//     `createComplianceReportCronJob` header comment for how that secret
//     is provisioned. Checked BEFORE the session cookie so the CronJob's
//     Pod (which carries no session) can reach this route at all.
//   - PUT (cadence): owner-only -- same discipline every other
//     org-security-relevant mutation in this app uses (ip-allowlist PUT,
//     branding PUT).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.COMPLIANCE_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-compliance-cron-secret");
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
      path: `/api/orgs/${id}/compliance-reports`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [reportsResult, cadenceResult] = await Promise.all([
    listComplianceReports(id),
    getComplianceCadence(id),
  ]);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/compliance-reports`,
    status: reportsResult.ok && cadenceResult.ok ? 200 : 502,
    requestId,
  });
  if (!reportsResult.ok) return NextResponse.json({ error: reportsResult.error }, { status: 502 });
  if (!cadenceResult.ok) return NextResponse.json({ error: cadenceResult.error }, { status: 502 });

  return NextResponse.json({
    namespace,
    cadence: cadenceResult.data,
    cronSchedule: cadenceResult.data ? CADENCE_CRON_SCHEDULE[cadenceResult.data.interval] : null,
    reports: reportsResult.data.map((r) => ({
      reportId: r.reportId,
      periodStart: r.periodStart,
      periodEnd: r.periodEnd,
      generatedAt: r.generatedAt,
      generatedBy: r.generatedBy,
      sections: r.sections,
      downloadUrl: `/api/orgs/${id}/compliance-reports/${r.reportId}?format=json`,
      csvUrl: `/api/orgs/${id}/compliance-reports/${r.reportId}?format=csv`,
      ndjsonUrl: `/api/orgs/${id}/compliance-reports/${r.reportId}?format=ndjson`,
    })),
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const cronAuthenticated = isCronAuthenticated(request);

  let actor: string;
  let namespace: string;

  if (cronAuthenticated) {
    // Unattended CronJob firing -- no session exists. `id` is used
    // directly as the namespace/org id, matching this route's own
    // documented fallback (and lib/scheduled-jobs.ts's
    // `buildComplianceReportCommand`, which always targets
    // `/api/orgs/${orgId}` where `orgId` was the namespace the CronJob
    // itself was created in).
    actor = "compliance-report-cronjob";
    const orgResult = await getOrg(id);
    namespace = orgResult.ok && orgResult.data ? orgResult.data.namespace : id;
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
    namespace = orgResult.data ? orgResult.data.namespace : id;

    const access = await requireRoleIn(session, namespace, "member");
    if (!access.ok) {
      writeAuditLogEntry({
        orgId: id,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/orgs/${id}/compliance-reports`,
        status: 403,
        requestId,
      });
      return access.response!;
    }
  }

  const body = await request.json().catch(() => ({}) as unknown);
  const explicitStart = typeof (body as Record<string, unknown>)?.periodStart === "string"
    ? ((body as Record<string, unknown>).periodStart as string)
    : null;
  const explicitEnd = typeof (body as Record<string, unknown>)?.periodEnd === "string"
    ? ((body as Record<string, unknown>).periodEnd as string)
    : null;

  let periodStart: string;
  let periodEnd: string;
  if (explicitStart && explicitEnd) {
    if (Number.isNaN(Date.parse(explicitStart)) || Number.isNaN(Date.parse(explicitEnd))) {
      return NextResponse.json({ error: "periodStart/periodEnd must be valid RFC3339 timestamps" }, { status: 400 });
    }
    if (Date.parse(explicitStart) >= Date.parse(explicitEnd)) {
      return NextResponse.json({ error: "periodStart must be before periodEnd" }, { status: 400 });
    }
    periodStart = explicitStart;
    periodEnd = explicitEnd;
  } else {
    // No explicit period given -- fall back to this org's own set
    // cadence (weekly/monthly trailing window), or a plain trailing-7-day
    // default for an org that has never set one, so "generate now" always
    // has a well-defined, real period to compute the report for.
    const cadenceResult = await getComplianceCadence(id);
    const interval: ComplianceCadenceInterval =
      cadenceResult.ok && cadenceResult.data ? cadenceResult.data.interval : "weekly";
    const period = periodForCadence(interval);
    periodStart = period.periodStart;
    periodEnd = period.periodEnd;
  }

  const result = await generateComplianceReport({
    orgId: id,
    namespace,
    periodStart,
    periodEnd,
    generatedBy: actor,
  });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/compliance-reports`,
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ report: result.data }, { status: 201 });
}

export async function PUT(
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

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/compliance-reports`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const interval = body?.interval;
  if (interval !== "weekly" && interval !== "monthly") {
    return NextResponse.json({ error: "interval must be 'weekly' or 'monthly'" }, { status: 400 });
  }

  const result = await setComplianceCadence(id, interval, actor);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/compliance-reports`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    cadence: result.data,
    cronSchedule: CADENCE_CRON_SCHEDULE[result.data.interval],
  });
}
