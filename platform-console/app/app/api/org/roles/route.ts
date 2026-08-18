import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { getOrgRoleAssignments, requireRole, ROLES, setOrgRole, type Role } from "@/lib/authz";

// Backs the owner-only /org page (app/org/page.tsx). Both GET and POST
// here are owner-gated -- not just the page's own UI check -- so the real
// enforcement boundary is this route, regardless of what the page's nav
// or client rendering happens to show. Runs on the Node.js runtime
// (default for route handlers), same as every other /api/* route in this
// tree that calls into lib/k8s.ts.

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
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/org/roles",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getOrgRoleAssignments();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/org/roles",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ assignments: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Changing another user's role is itself owner-gated -- same
  // requireRole boundary as the routes this page manages access to.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/org/roles",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const identifier = typeof body?.identifier === "string" ? body.identifier.trim() : "";
  const role = typeof body?.role === "string" ? (body.role as Role) : ("" as Role);

  if (!identifier || !ROLES.includes(role)) {
    return NextResponse.json(
      { error: `identifier is required and role must be one of: ${ROLES.join(", ")}` },
      { status: 400 },
    );
  }

  const result = await setOrgRole(identifier, role);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/org/roles",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ assignments: result.data });
}
