import { NextRequest, NextResponse } from "next/server";
import { isSecureRequest } from "@/lib/request-meta";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getPartner, partnerManagesOrg, formatPartnerSwitchActor } from "@/lib/partners";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, SESSION_MAX_AGE, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { startImpersonation } from "@/lib/impersonation";

// The no-re-authentication context switch a Partner/MSP console needs:
// validate that the requesting session's target partner actually
// manages this org (never trust `orgId` off the request path alone),
// then hand back per-org context through the SAME two real primitives
// this app already has for "act inside a different org without a new
// login" -- there is no second, per-org session-cookie shape in this
// codebase (every session -- local-admin/gotrue/oidc-external/api-key
// -- shares the ONE `platform_console_session` cookie; per-org scoping
// is enforced by lib/authz.ts's requireRoleIn reading the target org's
// own namespace-local roles ConfigMap, not by a distinct cookie per
// org):
//
//   1. Re-set the SAME `platform_console_session` cookie
//      (SESSION_COOKIE_NAME) this app already uses for every session,
//      refreshed to a fresh SESSION_MAX_AGE window -- the real,
//      concrete meaning of "the org-scoped session cookie the app
//      already uses per-org" in an app with exactly one session-cookie
//      shape: no new JWT claim, no second cookie, just the existing
//      mechanism re-applied for this org-switch action.
//   2. Start a REAL lib/impersonation.ts session scoped to `orgId` --
//      the exact mechanism app/api/support/impersonate/route.ts already
//      uses to give an authenticated identity live, time-boxed access
//      to act inside an org other than its own, and the exact mechanism
//      middleware.ts's `x-impersonation-session` header resolution
//      (lib/impersonation.ts's resolveRequestImpersonation) already
//      wires into the SAME hash-chained audit_log every other
//      privileged action lands in. The client attaches the returned
//      `impersonationSession.id` as `x-impersonation-session` on
//      subsequent requests scoped to this org, same as an admin's
//      browser already does after POST /api/support/impersonate.
//
// This route's OWN audit_log row is tagged with
// lib/partners.ts's `formatPartnerSwitchActor` -- the same
// "fold the switch's context into the actor string" convention
// lib/impersonation.ts's own `formatImpersonationActor` already
// applies for a live-request-path admin-impersonation switch.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ partnerId: string; orgId: string }> },
) {
  const { partnerId, orgId } = await params;
  const requestId = newRequestId();
  const routePath = `/api/partners/${partnerId}/switch-org/${orgId}`;

  const sessionToken = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = await requireSession(request);
  if (!session || !sessionToken) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  // Same platform-admin boundary as the rest of the Partner surface --
  // there is no distinct "partner user" identity in this codebase's
  // session model (every session is local-admin/gotrue/oidc-external/
  // api-key), so a reseller's staff account is provisioned the same way
  // any other platform operator is: a real entry in the platform's own
  // `platform-console-org-roles` ConfigMap. No new authz primitive.
  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: routePath,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const partnerResult = await getPartner(partnerId);
  if (!partnerResult.ok) {
    return NextResponse.json({ error: partnerResult.error }, { status: 502 });
  }
  const partner = partnerResult.data;
  if (!partner) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: routePath,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "partner not found" }, { status: 404 });
  }

  if (!partnerManagesOrg(partner, orgId)) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: routePath,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      { error: `partner '${partnerId}' does not manage org '${orgId}'` },
      { status: 403 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: routePath,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const body = await request.json().catch(() => null);
  const reason =
    typeof body?.reason === "string" && body.reason.trim()
      ? body.reason.trim()
      : `partner console switch via partner '${partnerId}'`;

  const impersonationResult = await startImpersonation(actor, orgId, reason);
  if (!impersonationResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: routePath,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: impersonationResult.error }, { status: 502 });
  }

  // Tag this route's own audit row with the same "fold switch context
  // into the actor string" convention lib/impersonation.ts's own
  // formatImpersonationActor applies -- see this file's header comment.
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor: formatPartnerSwitchActor(actor, partnerId, orgId),
    method: "POST",
    path: routePath,
    status: 200,
    requestId,
    impersonatedBy: actor,
    impersonationSessionId: impersonationResult.data.id,
  });

  const response = NextResponse.json({
    org,
    partnerId,
    impersonationSession: impersonationResult.data,
  });
  // Re-set the same session cookie the app already uses per-org,
  // refreshed to a fresh window -- see this file's header comment for
  // why this is the real, concrete meaning of "org-scoped session
  // cookie" in an app with exactly one session-cookie shape.
  response.cookies.set(SESSION_COOKIE_NAME, sessionToken, {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  return response;
}
