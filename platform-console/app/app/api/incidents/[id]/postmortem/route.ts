import { NextRequest, NextResponse } from "next/server";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { generatePostmortem, getPostmortem, finalizePostmortem } from "@/lib/postmortems";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real Incident Postmortem / RCA document endpoint -- see
// lib/postmortems.ts's own header comment for the compliance gap this
// closes (auto-drafted timeline/duration/severity/credit from data this
// repo already tracks, human-authored rootCause/remediation via PATCH,
// never a fabricated draft).
//
// Auth, same app-level RBAC boundary as GET/POST /api/incidents (this is
// an incident sub-resource, not scoped to one customer org's own
// membership):
//   - GET: any authenticated member (viewer and up) -- a customer
//     reviewing their own incident's postmortem needs the same
//     viewer-level floor GET /api/incidents already uses.
//   - POST (generate/refresh the factual draft) and PATCH (record
//     rootCause/remediation, optionally finalize): platform-console's own
//     "owner" role, the identical floor POST /api/incidents' annotation
//     endpoint already requires for the same reason -- writing an
//     incident's compliance record is a platform-operator action.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
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
  const path = `/api/incidents/${id}/postmortem`;

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getPostmortem(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: result.ok ? (result.ok && result.data ? 200 : 404) : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json(
      { error: `no postmortem exists for incident '${id}' -- POST this endpoint to generate one` },
      { status: 404 },
    );
  }
  return NextResponse.json({ postmortem: result.data });
}

// POST -- generates (or refreshes the factual fields of) this incident's
// postmortem draft: real timeline, severity, duration, SLA-breach status,
// and the illustrative credit amount, all re-derived fresh from
// lib/incidents.ts and lib/orgs.ts/lib/tiers.ts on every call. Never
// touches rootCause/remediation/status once a draft exists -- see
// lib/postmortems.ts's generatePostmortem doc comment.
export async function POST(
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
  const path = `/api/incidents/${id}/postmortem`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await generatePostmortem(id, actor);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path,
    status: result.ok ? 200 : 502,
    requestId,
    postmortemIncidentId: id,
    postmortemAction: result.ok ? "postmortem_generated" : undefined,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ postmortem: result.data });
}

const VALID_PATCH_KEYS = new Set(["rootCause", "remediation", "status"]);

// PATCH -- the only path that ever writes rootCause/remediation, and the
// only path that can move status to "final" (requires both fields
// non-empty -- see lib/postmortems.ts's finalizePostmortem doc comment).
// Audited as a SEPARATE `postmortem_finalized` event from POST's
// `postmortem_generated`, same "distinct auditable events for the
// automatic draft vs. the human sign-off" convention
// app/api/orgs/[id]/sla-credits/route.ts's GET/POST split already
// establishes for "credit computed" vs. "credit applied".
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
  const path = `/api/incidents/${id}/postmortem`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  if (!body || typeof body !== "object") {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path,
      status: 400,
      requestId,
      postmortemIncidentId: id,
    });
    return NextResponse.json({ error: "request body must be a JSON object" }, { status: 400 });
  }

  for (const key of Object.keys(body)) {
    if (!VALID_PATCH_KEYS.has(key)) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "PATCH",
        path,
        status: 400,
        requestId,
        postmortemIncidentId: id,
      });
      return NextResponse.json(
        { error: `unsupported field '${key}' -- may only PATCH: ${Array.from(VALID_PATCH_KEYS).join(", ")}` },
        { status: 400 },
      );
    }
  }

  const rootCause = typeof body.rootCause === "string" ? body.rootCause : undefined;
  const remediation = typeof body.remediation === "string" ? body.remediation : undefined;

  if (body.status !== undefined && body.status !== "final") {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path,
      status: 400,
      requestId,
      postmortemIncidentId: id,
    });
    return NextResponse.json(
      { error: "status may only be set to 'final' via PATCH -- there is no supported un-finalize path" },
      { status: 400 },
    );
  }
  const markFinal = body.status === "final";

  const result = await finalizePostmortem({ incidentId: id, rootCause, remediation, markFinal, actor });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PATCH",
    path,
    status: result.ok ? 200 : 502,
    requestId,
    postmortemIncidentId: id,
    postmortemAction: result.ok && markFinal ? "postmortem_finalized" : undefined,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ postmortem: result.data });
}
