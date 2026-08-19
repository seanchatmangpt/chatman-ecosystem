import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  createFreezeWindow,
  deleteFreezeWindow,
  listFreezeWindows,
  validateFreezeWindowInput,
} from "@/lib/freeze-windows";

// Real deployment / change-freeze window CRUD (lib/freeze-windows.ts,
// SOC2 CC8 / ITIL change management -- see that module's own header
// comment for why this exists and what it enforces).
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     seeing upcoming/active freeze windows is not a privileged action,
//     and the console-wide banner (every other page) needs this too.
//   - POST/DELETE: owner of THIS org specifically, checked against that
//     org's OWN namespace-local `platform-console-org-roles` ConfigMap
//     via lib/authz.ts's requireRoleIn -- declaring or removing a
//     change-freeze window is the same class of decision as pinning a
//     region or setting SLA terms.

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

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim() ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/freeze-windows",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listFreezeWindows(orgId);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/freeze-windows",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    windows: [...result.data].sort((a, b) => a.startsAt.localeCompare(b.startsAt)),
  });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/freeze-windows",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const startsAt = typeof body?.startsAt === "string" ? body.startsAt.trim() : "";
  const endsAt = typeof body?.endsAt === "string" ? body.endsAt.trim() : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";
  const allowEmergencyOverride = body?.allowEmergencyOverride === true;

  const validationError = validateFreezeWindowInput({ startsAt, endsAt, reason });
  if (validationError) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/freeze-windows",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const result = await createFreezeWindow({
    orgId,
    startsAt,
    endsAt,
    reason,
    createdBy: actor,
    allowEmergencyOverride,
  });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/freeze-windows",
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ window: result.data }, { status: 201 });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim() ?? "";
  const id = request.nextUrl.searchParams.get("id")?.trim() ?? "";
  if (!orgId || !id) {
    return NextResponse.json(
      { error: "orgId and id query parameters are required" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/freeze-windows",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await deleteFreezeWindow(orgId, id);
  const status = !result.ok ? ("error" in result && result.error === "not_found" ? 404 : 502) : 200;
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/freeze-windows",
    status,
    requestId,
  });
  if (!result.ok) {
    if (result.error === "not_found") {
      return NextResponse.json({ error: "freeze window not found" }, { status: 404 });
    }
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deleted: true });
}
