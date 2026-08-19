import { NextRequest, NextResponse } from "next/server";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import {
  annotateIncident,
  listIncidents,
  reconcileIncidents,
  type IncidentSeverity,
} from "@/lib/incidents";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { dispatchToRoutedTargets } from "@/lib/alert-routing";

// Real SLA incident tracker endpoint -- see lib/incidents.ts's own header
// comment for the gap this closes. Incidents are DERIVED from real
// Prometheus `up` spans (lib/status-page.ts's getComponentDownWindows),
// never hand-entered wholesale; this route's POST is deliberately narrow
// (root-cause/severity/org annotation on an EXISTING reconciler-created
// row only, see lib/incidents.ts's annotateIncident doc comment) rather
// than a general incident-creation endpoint.
//
// Auth model, same app-level RBAC boundary as every other route in this
// tree (lib/authz.ts, layered on top of -- never replacing -- the
// console's own ServiceAccount k8s RBAC):
//   - GET: any authenticated member (viewer and up) -- reading the
//     incident timeline is not a privileged action, same floor
//     GET /api/audit and GET /api/orgs/[id]/sla already use.
//   - POST: platform-console's own "owner" role specifically (this
//     codebase's org-scoped role model tops out at "owner", the
//     admin-only floor the spec calls for -- there is no separate
//     platform-wide "admin" role distinct from an org's own owner role;
//     platform-console's own namespace roles are the correct floor here
//     because incident annotation is a platform-operator action, not
//     scoped to one customer org's own membership the way
//     PUT /api/orgs/[id]/sla is).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const SEVERITIES: IncidentSeverity[] = ["minor", "major", "critical"];

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this 403 branch fires before ?orgId= is parsed below
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/incidents",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const { searchParams } = new URL(request.url);
  const orgId = searchParams.get("orgId") ?? undefined;
  const componentId = searchParams.get("componentId") ?? undefined;
  const from = searchParams.get("from") ?? undefined;
  const to = searchParams.get("to") ?? undefined;
  const limitRaw = Number(searchParams.get("limit") ?? "50");
  const offsetRaw = Number(searchParams.get("offset") ?? "0");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(1, limitRaw), 200) : 50;
  const offset = Number.isFinite(offsetRaw) ? Math.max(0, offsetRaw) : 0;

  // Manual reconcile trigger -- `?reconcile=1h` (a PromQL-style duration on
  // how far back to look from now) runs a real reconcile pass before
  // reading the list back, so an operator can force a fresh derivation
  // instead of waiting for the scheduled cron reconciler (RemoteTrigger/
  // CronCreate wiring, external to this route). Optional -- GET works
  // without it, reading whatever the last reconcile run (cron or manual)
  // already persisted.
  const reconcileParam = searchParams.get("reconcile");
  if (reconcileParam) {
    const hoursMatch = /^(\d+)h$/.exec(reconcileParam);
    const hours = hoursMatch ? Number(hoursMatch[1]) : 1;
    const end = new Date();
    const start = new Date(end.getTime() - hours * 3_600_000);
    const reconcileResult = await reconcileIncidents(start, end);
    if (!reconcileResult.ok) {
      writeAuditLogEntry({
        orgId: orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/incidents",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: reconcileResult.error }, { status: 502 });
    }
  }

  const result = await listIncidents({ orgId, componentId, from, to, limit, offset });
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/incidents",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this 403 branch fires before body.orgId is parsed below
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/incidents",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const id = typeof body?.id === "string" ? body.id.trim() : "";
  if (!id) {
    writeAuditLogEntry({
      // org-agnostic: body.orgId hasn't been parsed yet at this point
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/incidents",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "id is required (the incident row to annotate)" }, { status: 400 });
  }

  const rootCause = typeof body?.rootCause === "string" ? body.rootCause.trim() : undefined;
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : undefined;
  let severity: IncidentSeverity | undefined;
  if (body?.severity !== undefined) {
    if (typeof body.severity !== "string" || !SEVERITIES.includes(body.severity as IncidentSeverity)) {
      writeAuditLogEntry({
        orgId: orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/incidents",
        status: 400,
        requestId,
      });
      return NextResponse.json(
        { error: `severity must be one of: ${SEVERITIES.join(", ")}` },
        { status: 400 },
      );
    }
    severity = body.severity as IncidentSeverity;
  }

  const result = await annotateIncident({ id, rootCause, severity, orgId });
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/incidents",
    status: result.ok ? (result.data ? 200 : 404) : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "incident not found" }, { status: 404 });
  }

  // Additive: per-org Alert-Routing -- only fireable once an incident is
  // actually annotated with an orgId (an incident's `org_id` starts
  // `null` at reconcile time -- see lib/incidents.ts's header comment --
  // so this route's own POST is the first point an incident is ever
  // attributable to a real org), alongside whatever org-wide webhook
  // subscriptions already exist.
  if (result.data.orgId) {
    dispatchToRoutedTargets(result.data.orgId, "incident", {
      incidentId: result.data.id,
      componentId: result.data.componentId,
      severity: result.data.severity,
      status: result.data.status,
      startedAt: result.data.startedAt,
      resolvedAt: result.data.resolvedAt,
    }).catch((err) => {
      console.error(`[api/incidents] alert-routing dispatch failed for incident ${result.data!.id}:`, err);
    });
  }

  return NextResponse.json({ incident: result.data });
}
