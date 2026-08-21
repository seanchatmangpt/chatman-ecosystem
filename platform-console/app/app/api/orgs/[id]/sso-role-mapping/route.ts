import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSsoGroupMappings, setOrgSsoGroupMappings } from "@/lib/orgs";
import { normalizeSsoGroupMappings, validateSsoGroupMappings } from "@/lib/sso-role-mapping";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, config-only SSO group -> app role mapping surface -- the org's
// own declared statement of intent GET /api/orgs/[id]/sso-role-drift
// diffs against real, live role assignments. See
// lib/sso-role-mapping.ts's module doc for the full, honest scope
// boundary (this route never provisions/deprovisions a role from a live
// IdP group claim -- it only records what the org SAYS its mapping is).
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) -- the
//     configured mapping set is not itself a secret, same posture as
//     GET /api/orgs/[id]/saml-config.
//   - PUT: owner of THIS org specifically, gated behind the SAME
//     maker-checker `sso.role-mapping.update` approval workflow
//     `pricing.override`/`freeze.override` already use -- one owner's
//     own assertion that a mapping is correct is never sufficient by
//     itself to bind a record a security review board will later trust;
//     a second, distinct owner-role approver must sign off first.

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
      path: `/api/orgs/${id}/sso-role-mapping`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const mappingsResult = await getOrgSsoGroupMappings(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/sso-role-mapping`,
    status: mappingsResult.ok ? 200 : 502,
    requestId,
  });
  if (!mappingsResult.ok) {
    return NextResponse.json({ error: mappingsResult.error }, { status: 502 });
  }
  return NextResponse.json({ mappings: mappingsResult.data });
}

export async function PUT(
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sso-role-mapping`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const rawMappings = body?.mappings;

  const validationError = validateSsoGroupMappings(rawMappings);
  if (validationError) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sso-role-mapping`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }
  const requestedMappings = normalizeSsoGroupMappings(rawMappings as unknown[]);

  const approval = await requireApproval({
    action: "sso.role-mapping.update",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedSsoGroupMappings: requestedMappings },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sso-role-mapping`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sso-role-mapping`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "sso.role-mapping.update requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize this ` +
          "mapping set, then retry PUT.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists -- bind exactly what was actually
  // approved (resourcePayload.requestedSsoGroupMappings on the approved
  // row), not whatever the caller happens to resend, same "bind the
  // approved payload, not the resent one" discipline
  // PUT /api/orgs/[id]/pricing-override already establishes.
  const approvedMappings =
    approval.approval.resourcePayload?.requestedSsoGroupMappings ?? requestedMappings;

  const result = await setOrgSsoGroupMappings(id, approvedMappings);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/sso-role-mapping`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({
    applied: true,
    mappings: approvedMappings,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
