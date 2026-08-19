import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { listOrgs } from "@/lib/orgs";
import { listAccessReviewSummaries } from "@/lib/access-reviews";

// GET /api/access-reviews: cross-org compliance-dashboard feed --
// every org's last-review recency, sorted most-overdue first, so a
// SOC2/ISO27001 compliance owner can see at a glance which orgs are
// past the ACCESS_REVIEW_OVERDUE_DAYS (90-day / quarterly) threshold.
// Platform-owner-gated (requireRole, not requireRoleIn -- this reads
// across every customer org, not one org's own namespace, matching the
// same platform-wide boundary /api/roles and /api/orgs already draw).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/access-reviews",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/access-reviews",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }

  const summariesResult = await listAccessReviewSummaries(orgsResult.data.map((o) => o.id));

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/access-reviews",
    status: summariesResult.ok ? 200 : 502,
    requestId,
  });

  if (!summariesResult.ok) {
    return NextResponse.json({ error: summariesResult.error }, { status: 502 });
  }
  return NextResponse.json({ reviews: summariesResult.data });
}
