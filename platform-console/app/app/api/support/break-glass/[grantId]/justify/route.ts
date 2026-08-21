import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { fileBreakGlassJustification } from "@/lib/break-glass";

// Mandatory post-hoc justification endpoint: the on-call engineer who
// opened a break-glass grant explains, after the fact, what they did and
// why -- and in the same call, lib/break-glass.ts's
// fileBreakGlassJustification opens the second-approver review
// (`"break-glass.justification-review"`) that closes the compensating
// two-person-integrity loop this control depends on. Platform-admin
// only, same rank as opening the grant in the first place.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ grantId: string }> },
) {
  const { grantId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/support/break-glass/${grantId}/justify`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const justification = typeof body?.justification === "string" ? body.justification.trim() : "";
  if (!justification) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/support/break-glass/${grantId}/justify`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "justification is required" }, { status: 400 });
  }

  const result = await fileBreakGlassJustification({ grantId, filedBy: actor, justification });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/support/break-glass/${grantId}/justify`,
    status: result.ok ? 200 : 400,
    requestId,
    orgId: result.ok ? result.data.grant.targetOrgId : undefined,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({
    breakGlassGrant: result.data.grant,
    approvalRequestId: result.data.approvalRequestId,
  });
}
