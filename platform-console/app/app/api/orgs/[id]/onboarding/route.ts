import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { runOnboardingChecks } from "@/lib/onboarding";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real onboarding-progress endpoint: computes the fixed, ordered
// checklist in lib/onboarding.ts against this org's REAL, live platform
// state (API keys, Projects, backup Jobs, namespace-local role
// assignments, custom-role grants, SLA/region fields) -- never a
// self-reported checkbox. No new persisted completion state exists
// anywhere, so this route is a pure read: every call re-derives the
// checklist fresh, and there is nothing here for a customer or CSM to
// fake.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route under
// /api/orgs/[id]/*: GET is available to any authenticated member of THIS
// org (viewer and up) -- reading your own org's onboarding progress is
// not a privileged action, same floor as GET .../sla and GET .../region.

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

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/onboarding`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await runOnboardingChecks(orgResult.data);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/onboarding`,
    status: 200,
    requestId,
  });

  return NextResponse.json(result);
}
