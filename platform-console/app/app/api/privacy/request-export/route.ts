import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { createDsarRequest, runDsarExport } from "@/lib/dsar";

// Real GDPR Art.15 / CCPA "right to know" access-request endpoint --
// files a real, durable DSAR export request (lib/dsar.ts's
// `platform-console-dsar-requests` ConfigMap) and kicks the real
// background poller (lib/dsar.ts's `runDsarExport`, same tick-loop shape
// as lib/webhook-poller.ts) immediately rather than waiting for the next
// scheduled tick, so a caller who then polls GET /api/privacy/status
// right away sees real progress, not an idle "pending" for up to 10s.
//
// Owner-gated (org-scoped, same `requireRoleIn(..., "owner")` boundary
// DELETE /api/orgs/[id] and PUT /api/orgs/[id]/branding already use):
// reading BACK another data subject's full audit/membership/API-key
// footprint is at least as sensitive as any other owner-only export in
// this console. Deliberately NOT maker-checker gated -- unlike erasure,
// an access export changes no durable state and is exactly the kind of
// single-owner-authorized action lib/approval-workflow.ts's own header
// comment describes as already covered by lib/authz.ts alone.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  const subjectEmail = typeof body?.subjectEmail === "string" ? body.subjectEmail.trim() : "";

  if (!orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }
  if (!subjectEmail || !EMAIL_RE.test(subjectEmail)) {
    return NextResponse.json({ error: "subjectEmail is required and must be a valid email" }, { status: 400 });
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
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/privacy/request-export (org=${orgId})`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const created = await createDsarRequest({
    orgId,
    subjectEmail,
    kind: "export",
    requestedBy: actor,
  });
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/privacy/request-export (org=${orgId})`,
    status: created.ok ? 202 : 502,
    requestId,
  });
  if (!created.ok) {
    return NextResponse.json({ error: created.error }, { status: 502 });
  }

  // Fire the real export job now rather than waiting for the poller's
  // next tick -- deliberately not awaited: the route responds 202
  // immediately with the request id, and the caller polls
  // GET /api/privacy/status?requestId=... for real completion, the same
  // "accepted, not completed" contract DELETE /api/orgs/[id]'s pending-
  // approval 202 already establishes for a different reason.
  void runDsarExport(created.data.requestId);

  return NextResponse.json({ status: "pending", request: created.data }, { status: 202 });
}
