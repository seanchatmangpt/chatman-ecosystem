import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { SESSION_COOKIE_NAME, verifySessionToken, createOrgInviteToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Admin-triggered invite path (the second entry point the task requires,
// alongside pure self-service /signup): owner-only (this console's own
// platform-console-org-roles ConfigMap, same gate app/api/org/roles uses),
// mints a real signed, 7-day, single-purpose JWT (lib/session.ts's
// createOrgInviteToken) naming a suggested org name and seed role. The
// resulting link (`/org/invite?token=...`) is handed to the new customer
// out of band (email, etc.) -- this route does not send that email itself,
// same "no fabricated mail transport" disclosure lib/gotrue-auth.ts's own
// header comment already makes for this cluster.
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/org-invites",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const orgName = typeof body?.orgName === "string" ? body.orgName.trim() : "";
  const role = body?.role === "member" ? "member" : "owner";
  if (!orgName) {
    return NextResponse.json({ error: "orgName is required" }, { status: 400 });
  }

  const inviteToken = await createOrgInviteToken({ orgName, role, issuedBy: actor });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/org-invites",
    status: 201,
    requestId,
  });

  return NextResponse.json(
    { inviteToken, inviteUrl: `/org/invite?token=${encodeURIComponent(inviteToken)}` },
    { status: 201 },
  );
}
