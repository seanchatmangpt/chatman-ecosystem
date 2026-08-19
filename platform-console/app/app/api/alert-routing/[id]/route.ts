import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  ALERT_ROUTING_EVENT_TYPES,
  ALERT_ROUTING_TARGET_TYPES,
  deleteAlertRoutingRule,
  updateAlertRoutingRule,
  type AlertRoutingEventType,
  type AlertRoutingTargetType,
} from "@/lib/alert-routing";

// PATCH/DELETE one routing rule by id -- `[id]` is the RULE id (from
// GET/POST /api/alert-routing's own AlertRoutingRule.id), scoped by the
// required `orgId` query param the same way DELETE /api/webhooks scopes
// by `?id=`. Same org-scoped owner-only RBAC boundary as
// app/api/alert-routing/route.ts's POST -- see that route's header
// comment.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

type OrgAuthzResult =
  | { response: NextResponse; org?: undefined }
  | { org: { id: string; namespace: string }; response?: undefined };

async function resolveOrgAndAuthorize(
  request: NextRequest,
  session: SessionPayload,
  orgId: string,
): Promise<OrgAuthzResult> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return { response: NextResponse.json({ error: orgResult.error }, { status: 502 }) };
  }
  if (!orgResult.data) {
    return { response: NextResponse.json({ error: "org not found" }, { status: 404 }) };
  }
  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    return { response: access.response ?? NextResponse.json({ error: "forbidden" }, { status: 403 }) };
  }
  return { org: orgResult.data };
}

export async function PATCH(
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

  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId (string) is required in the request body" }, { status: 400 });
  }

  const authz = await resolveOrgAndAuthorize(request, session, orgId);
  if (authz.response) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/alert-routing/${id}`,
      status: authz.response.status,
      requestId,
    });
    return authz.response;
  }

  const eventType =
    body?.eventType !== undefined ? (body.eventType as AlertRoutingEventType) : undefined;
  const targetType =
    body?.targetType !== undefined ? (body.targetType as AlertRoutingTargetType) : undefined;
  const targetUrlOrAddress =
    typeof body?.targetUrlOrAddress === "string" ? body.targetUrlOrAddress.trim() : undefined;
  const enabled = typeof body?.enabled === "boolean" ? body.enabled : undefined;

  if (eventType !== undefined && !ALERT_ROUTING_EVENT_TYPES.includes(eventType)) {
    return NextResponse.json(
      { error: `eventType must be one of: ${ALERT_ROUTING_EVENT_TYPES.join(", ")}` },
      { status: 400 },
    );
  }
  if (targetType !== undefined && !ALERT_ROUTING_TARGET_TYPES.includes(targetType)) {
    return NextResponse.json(
      { error: `targetType must be one of: ${ALERT_ROUTING_TARGET_TYPES.join(", ")}` },
      { status: 400 },
    );
  }
  if (targetUrlOrAddress !== undefined && targetUrlOrAddress === "") {
    return NextResponse.json({ error: "targetUrlOrAddress may not be empty" }, { status: 400 });
  }

  const result = await updateAlertRoutingRule(orgId, id, {
    eventType,
    targetType,
    targetUrlOrAddress,
    enabled,
  });

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "PATCH",
    path: `/api/alert-routing/${id}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "rule not found" }, { status: 404 });
  }
  return NextResponse.json({ rule: result.data });
}

export async function DELETE(
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

  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query param is required" }, { status: 400 });
  }

  const authz = await resolveOrgAndAuthorize(request, session, orgId);
  if (authz.response) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/alert-routing/${id}`,
      status: authz.response.status,
      requestId,
    });
    return authz.response;
  }

  const result = await deleteAlertRoutingRule(orgId, id);

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/alert-routing/${id}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "rule not found" }, { status: 404 });
  }
  return NextResponse.json({ ok: true });
}
