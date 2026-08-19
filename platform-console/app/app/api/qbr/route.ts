import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { listLatestQbrBundles } from "@/lib/qbr";

// Platform-admin cross-org QBR dashboard endpoint -- every org's single
// most-recent Quarterly Business Review bundle, the same cross-org admin
// view shape GET /api/contract-renewals and GET /api/budget-alerts
// already establish for a platform-wide "owner" gate with no single-org
// membership boundary to check.
//
// GET only here: lists every org's latest bundle (or `latest: null` for
// an org that has never had one generated). Per-org history lives at
// GET /api/qbr/[orgId]; on-demand (re)generation lives at
// POST /api/qbr/[orgId]/generate -- matching this repo's own
// list-route-is-read-only / [id]-route-is-the-mutation convention (see
// GET /api/contract-renewals's own header comment for the same split).

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

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/qbr",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listLatestQbrBundles();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/qbr",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ bundles: result.data });
}
