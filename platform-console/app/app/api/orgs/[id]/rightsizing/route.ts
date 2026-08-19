import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getRightsizingDigest } from "@/lib/rightsizing";

// Real reserved-capacity / idle-waste rightsizing digest (AWS Trusted
// Advisor "low utilization" / GCP Recommender-style capability -- see
// lib/rightsizing.ts's own header comment for the full method): diffs
// this org's namespace's real live Pod resource *requests* against its
// real trailing-window average *usage* (the same Prometheus queries
// lib/invoice-preview.ts already issues for cost figures) and surfaces a
// concrete, dollar-denominated rightsizing recommendation wherever the
// idle gap is large and sustained. Computed live on every GET, never
// persisted -- same "no new storage" discipline as GET
// /api/orgs/[id]/usage-forecast: a read-only analytical view over data
// every other cost module in this tree already fetches, introducing no
// new k8s RBAC verb and no new ConfigMap.
//
// `id` resolution follows the same convention every other
// `/api/orgs/[id]/*` route in this tree uses (see
// app/api/orgs/[id]/cost-reports/route.ts's own header comment): resolve
// against the real `platform-console-orgs` registry first; when `id`
// doesn't resolve there, `id` is used directly as both the org id AND the
// k8s namespace.
//
// Auth: any authenticated member of this org (viewer and up) -- reading a
// savings recommendation derived entirely from this org's own real
// metered usage and its own real live Pod specs is not a privileged
// action, same posture as GET /api/orgs/[id]/cost-reports and GET
// /api/orgs/[id]/usage-forecast.
//
// `?windowLabel=`/`?windowHours=` override the default trailing 7-day
// window the spec calls for (PromQL duration literal + its numeric hour
// equivalent, same paired-params convention lib/invoice-preview.ts's
// callers already use); windowHours is clamped to [1, 720] (up to 30
// days) since it is also the divisor used to turn accumulated core-hours
// / GiB-hours back into an average instantaneous reservation-comparable
// figure -- a windowHours of 0 would divide by zero.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function parseWindow(request: NextRequest): { windowLabel: string; windowHours: number } {
  const windowLabel = request.nextUrl.searchParams.get("windowLabel") ?? "7d";
  const rawHours = request.nextUrl.searchParams.get("windowHours");
  let windowHours = 24 * 7;
  if (rawHours) {
    const n = Number(rawHours);
    if (Number.isFinite(n)) windowHours = Math.min(720, Math.max(1, Math.floor(n)));
  }
  return { windowLabel, windowHours };
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
      path: `/api/orgs/${id}/rightsizing`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const { windowLabel, windowHours } = parseWindow(request);
  const digest = await getRightsizingDigest([namespace], windowLabel, windowHours);

  const status = digest.errors.length > 0 && digest.results.length === 0 ? 502 : 200;

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/rightsizing`,
    status,
    requestId,
  });

  if (status === 502) {
    return NextResponse.json({ error: digest.errors[0]?.error ?? "rightsizing query failed" }, { status: 502 });
  }

  return NextResponse.json(digest);
}
