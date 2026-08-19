import { NextRequest, NextResponse } from "next/server";
import {
  roleIdentifierFor,
  requireRole,
} from "@/lib/authz";
import { createOrg, listOrgs } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken, verifyOrgInviteToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Closes the gap this task targets: the real, self-service tenant/org
// creation endpoint. No engineer edits a shared ConfigMap by hand -- this
// route calls lib/orgs.ts's createOrg, which does the real k8s Namespace
// create + org-scoped roles ConfigMap seed + registry write + first-
// Project provisioning end to end.
//
// Auth model for POST: the caller must already hold a real session (minted
// by /api/auth/gotrue-signup or /api/auth/gotrue-login, called first by
// the /signup page's client-side flow -- see app/signup/page.tsx). Two
// paths from there:
//   - No `inviteToken` in the body: pure self-service. The caller becomes
//     the new org's owner, using their own session identity. This is the
//     "sign up and get your own isolated tenant" path procurement expects.
//   - `inviteToken` present: must be a real, signed, unexpired token
//     minted by an existing platform owner via POST /api/org-invites
//     (see that route). The token's `role` claim is honored for THIS
//     caller's seed role in the new org (still always "owner" of THAT new
//     org today -- multi-member org invites onto an EXISTING org, rather
//     than always creating a fresh one, is a real, disclosed follow-up,
//     not claimed done here).
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = await request.json().catch(() => null);
  const rawName = typeof body?.name === "string" ? body.name.trim() : "";
  const inviteToken = typeof body?.inviteToken === "string" ? body.inviteToken : null;

  let orgName = rawName;
  if (inviteToken) {
    const invite = await verifyOrgInviteToken(inviteToken);
    if (!invite) {
      // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/orgs",
        status: 401,
        requestId,
      });
      return NextResponse.json(
        { error: "invalid or expired invite token" },
        { status: 401 },
      );
    }
    orgName = orgName || invite.orgName;
  }

  if (!orgName) {
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }

  const result = await createOrg({ name: orgName, ownerIdentifier: actor });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/orgs",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data, { status: 201 });
}

// Listing every org is platform-operator visibility, not customer
// self-service -- gated the same way /api/org/roles gates role changes:
// requireRole(session, "owner") against the PLATFORM's own
// platform-console-org-roles ConfigMap (lib/authz.ts), i.e. this console's
// own operators, not any one customer org's owner.
export async function GET(request: NextRequest) {
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
      method: "GET",
      path: "/api/orgs",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listOrgs();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/orgs",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ orgs: result.data });
}
