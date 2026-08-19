import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { createPartner, listPartners } from "@/lib/partners";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Partner/MSP Multi-Tenant Management Console -- CRUD entry point. Every
// verb here is admin-only, gated by the SAME `requirePlatformAdmin`
// (lib/authz.ts) boundary app/api/support/impersonate/route.ts already
// uses for its own platform-wide privileged action -- no new authz
// primitive introduced for this feature.

async function requireSession(request: NextRequest) {
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
      path: "/api/partners",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listPartners();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/partners",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ partners: result.data });
}

export async function POST(request: NextRequest) {
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
      path: "/api/partners",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const name = typeof body?.name === "string" ? body.name.trim() : "";
  const managedOrgIds = Array.isArray(body?.managedOrgIds)
    ? body.managedOrgIds.filter((o: unknown): o is string => typeof o === "string" && o.trim().length > 0)
    : [];

  if (!name) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/partners",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }

  const result = await createPartner({ name, managedOrgIds });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/partners",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ partner: result.data });
}
