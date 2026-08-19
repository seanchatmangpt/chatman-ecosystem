import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  ALERT_ROUTING_EVENT_TYPES,
  ALERT_ROUTING_TARGET_TYPES,
  createAlertRoutingRule,
  listAlertRoutingRules,
  type AlertRoutingEventType,
  type AlertRoutingTargetType,
} from "@/lib/alert-routing";

// Per-org Alert-Routing Rule Engine (event-type -> channel matrix):
// Enterprise-tier on-call routing control, PagerDuty/Datadog-style --
// distinct from the org-wide GET/POST /api/webhooks (which fans EVERY
// event out to one URL) and from /api/status/subscribe (which only
// covers public platform-status component changes). See
// lib/alert-routing.ts's header comment for the full design.
//
// Org-scoped RBAC, same boundary app/api/orgs/[id]/branding/route.ts
// establishes: checked against the target org's OWN namespace-local
// `platform-console-org-roles` ConfigMap via lib/authz.ts's
// requireRoleIn, never the platform's own roles -- an owner of org A can
// never read or write org B's routing rules.
//   - GET: any authenticated member of the org (viewer and up).
//   - POST: owner of the org specifically -- a routing rule is a real
//     exfiltration-adjacent destination (a security/billing event body
//     gets POSTed or emailed to whatever this rule names), same
//     sensitivity class /api/webhooks already treats as owner-only.

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

  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query param is required" }, { status: 400 });
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
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/alert-routing",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listAlertRoutingRules(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/alert-routing",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    rules: result.data,
    eventTypes: ALERT_ROUTING_EVENT_TYPES,
    targetTypes: ALERT_ROUTING_TARGET_TYPES,
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
    return NextResponse.json({ error: "orgId (string) is required" }, { status: 400 });
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
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/alert-routing",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const eventType =
    typeof body?.eventType === "string" ? (body.eventType as AlertRoutingEventType) : ("" as AlertRoutingEventType);
  const targetType =
    typeof body?.targetType === "string"
      ? (body.targetType as AlertRoutingTargetType)
      : ("" as AlertRoutingTargetType);
  const targetUrlOrAddress =
    typeof body?.targetUrlOrAddress === "string" ? body.targetUrlOrAddress.trim() : "";
  const enabled = typeof body?.enabled === "boolean" ? body.enabled : true;

  if (!ALERT_ROUTING_EVENT_TYPES.includes(eventType)) {
    return NextResponse.json(
      { error: `eventType must be one of: ${ALERT_ROUTING_EVENT_TYPES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!ALERT_ROUTING_TARGET_TYPES.includes(targetType)) {
    return NextResponse.json(
      { error: `targetType must be one of: ${ALERT_ROUTING_TARGET_TYPES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!targetUrlOrAddress) {
    return NextResponse.json({ error: "targetUrlOrAddress is required" }, { status: 400 });
  }

  if (targetType === "email") {
    // Same conservative shape check as every other email input in this
    // codebase's route handlers -- not a full RFC 5322 validator, just
    // enough to reject an obviously malformed address before it is
    // persisted as a delivery target.
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(targetUrlOrAddress)) {
      return NextResponse.json({ error: "targetUrlOrAddress must be a valid email address" }, { status: 400 });
    }
  } else {
    let parsedUrl: URL;
    try {
      parsedUrl = new URL(targetUrlOrAddress);
    } catch {
      return NextResponse.json({ error: "targetUrlOrAddress must be a valid absolute URL" }, { status: 400 });
    }
    if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
      return NextResponse.json({ error: "targetUrlOrAddress must use http or https" }, { status: 400 });
    }
  }

  const result = await createAlertRoutingRule(orgId, {
    eventType,
    targetType,
    targetUrlOrAddress,
    enabled,
    createdBy: actor,
  });

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/alert-routing",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ rule: result.data }, { status: 201 });
}
