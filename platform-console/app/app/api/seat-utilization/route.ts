import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import {
  appendSeatUtilizationSnapshot,
  generateSeatUtilizationSnapshot,
  listSeatUtilizationSnapshots,
} from "@/lib/seat-utilization-report";

// Real Scheduled Seat/License Utilization Report for Procurement --
// distinct from app/api/access-reviews (security-owner named-user
// attestation) and app/api/qbr (business-review bundle): this is the
// narrow purchased-vs-active-seat, invited-unaccepted, and stale-seat
// cost-waste artifact a Fortune-5 Procurement/IT-Asset-Management team
// pulls for a quarterly seat-based-contract true-up review.
//
// GET  -- lists this org's real snapshot history (oldest first), the
//         read side of the "seat-utilization-snapshot" lib/scheduled-jobs.ts
//         CronJob command (monthly cadence). Any authenticated member of
//         the org (viewer and up) may read it -- same posture as
//         GET /api/orgs/[id]/cost-reports.
// POST -- triggers generation of ONE fresh snapshot on demand, appended
//         to the same history. Two distinct callers, same as
//         POST /api/internal/cost-report-snapshot's own dual-purpose
//         precedent within a single route (this capability's own spec
//         asks for one file, not a second /api/internal/* route):
//           1. The unattended monthly CronJob, authenticated by the
//              fixed shared-secret header below -- no session, carries
//              only its own namespace.
//           2. An interactive owner-role session, for "run this now"
//              on-demand generation from the console UI -- authenticated
//              the normal session-cookie way, requires owner in the
//              target org.

function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.SEAT_UTILIZATION_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-seat-utilization-cron-secret");
  return presented === expected;
}

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : orgId;

  const access = await requireRoleIn(session, namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/seat-utilization",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listSeatUtilizationSnapshots(orgId);

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/seat-utilization",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ snapshots: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();

  if (isCronAuthenticated(request)) {
    // Scheduled-CronJob path -- `orgId` travels as a header, threaded in
    // by lib/scheduled-jobs.ts's buildContainerCommand
    // ("seat-utilization-snapshot" case) from this CronJob's OWN
    // namespace -- validated here against the same fixed
    // SCHEDULABLE_NAMESPACES allowlist the CronJob itself was created
    // against, never trusted as free-form request text. This namespace
    // doubles as the orgId this report is keyed by, the same
    // "namespace IS the single-tenant orgId" fallback
    // generateSeatUtilizationSnapshot's own getOrg resolution already
    // uses when an id doesn't resolve in the orgs registry.
    const namespace = request.headers.get("x-seat-utilization-namespace") ?? "";
    if (!isSchedulableNamespace(namespace)) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor: "seat-utilization-snapshot-cronjob",
        method: "POST",
        path: "/api/seat-utilization",
        status: 400,
        requestId,
      });
      return NextResponse.json(
        {
          error:
            "x-seat-utilization-namespace header must be one of the platform's own namespaces",
        },
        { status: 400 },
      );
    }

    const snapshotResult = await generateSeatUtilizationSnapshot(namespace);
    if (!snapshotResult.ok) {
      writeAuditLogEntry({
        orgId: namespace,
        timestamp: new Date().toISOString(),
        actor: "seat-utilization-snapshot-cronjob",
        method: "POST",
        path: "/api/seat-utilization",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: snapshotResult.error }, { status: 502 });
    }

    const appendResult = await appendSeatUtilizationSnapshot(snapshotResult.data);
    writeAuditLogEntry({
      orgId: namespace,
      timestamp: new Date().toISOString(),
      actor: "seat-utilization-snapshot-cronjob",
      method: "POST",
      path: "/api/seat-utilization",
      status: appendResult.ok ? 201 : 502,
      requestId,
    });
    if (!appendResult.ok) {
      return NextResponse.json({ error: appendResult.error }, { status: 502 });
    }
    return NextResponse.json({ snapshot: appendResult.data.at(-1) }, { status: 201 });
  }

  // On-demand path -- an interactive owner-role session asking for a
  // fresh snapshot right now (e.g. right before a procurement review
  // meeting, rather than waiting for the next monthly CronJob firing).
  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : orgId;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/seat-utilization",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const snapshotResult = await generateSeatUtilizationSnapshot(orgId);
  if (!snapshotResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/seat-utilization",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: snapshotResult.error }, { status: 502 });
  }

  const appendResult = await appendSeatUtilizationSnapshot(snapshotResult.data);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/seat-utilization",
    status: appendResult.ok ? 201 : 502,
    requestId,
  });
  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshot: appendResult.data.at(-1) }, { status: 201 });
}
