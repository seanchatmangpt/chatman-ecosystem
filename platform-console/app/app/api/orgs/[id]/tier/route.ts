import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { listProjects, setProjectTier } from "@/lib/k8s";
import { requireApproval } from "@/lib/approval-workflow";
import { isProjectTier, tierAtLeast, SEAT_LIMITS, type ProjectTier } from "@/lib/tiers";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real maker-checker-gated org tier downgrade: this codebase has no
// separate "org tier" field to mutate (lib/orgs.ts's getOrgProjectTier
// documents why -- an org's tier is always re-derived live from the
// HIGHEST `TIER_LABEL` among the real Project CRs in its namespace, so
// there is nothing to drift). A downgrade therefore means: patch every
// Project in this org's namespace currently ABOVE the requested tier
// down to it, via the same setProjectTier (lib/k8s.ts) the sibling
// app/api/projects/[name]/tier/route.ts already uses for a single
// Project -- but only after a second, distinct owner-role approver
// signs off, since this is a real revenue-reducing entitlement change
// (fewer seats via SEAT_LIMITS, a smaller ResourceQuota ceiling) for a
// paying customer, the same class of decision `org.delete` is already
// gated behind.
//
// A tier CHANGE that is not a downgrade (equal or higher rank) is not
// gated -- only a downgrade needs a second sign-off; nothing here blocks
// an upgrade.
//
// Flow, same retry-based convention as org.delete / quota.override:
//   1. Caller must hold role >= owner IN THIS ORG's own namespace.
//   2. requireApproval checks for a fresh (<=24h) approved
//      `tier.downgrade` row for this org id. None exists on the first
//      call -- a pending request (carrying the requested tier as
//      `resourcePayload.requestedTier`) is created and this route
//      returns 202 instead of touching any Project.
//   3. A second, distinct owner approves via POST /api/approvals/[id].
//   4. The original caller retries POST -- requireApproval now finds the
//      fresh approved row and every Project above the approved tier is
//      patched down to it. SEAT_LIMITS reconciliation needs no separate
//      write: it is read live off the (now-downgraded) tier by every
//      caller (e.g. app/api/orgs/[id]/invites/route.ts), same as the
//      ResourceQuota ceiling already re-derives live inside
//      setProjectTier itself.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

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

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tier`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const tier = typeof body?.tier === "string" ? body.tier.trim() : "";
  if (!tier || !isProjectTier(tier)) {
    return NextResponse.json(
      { error: `invalid tier '${tier}' -- must be starter, pro, or enterprise` },
      { status: 400 },
    );
  }
  const requestedTier: ProjectTier = tier;

  const currentTierResult = await getOrgProjectTier(org.namespace);
  if (!currentTierResult.ok) {
    return NextResponse.json({ error: currentTierResult.error }, { status: 502 });
  }
  const currentTier = currentTierResult.data;

  if (tierAtLeast(requestedTier, currentTier)) {
    // Not a downgrade (same tier, or an upgrade) -- no approval needed.
    // Applies immediately by patching every Project in this org's
    // namespace up to the requested tier, same real setProjectTier
    // primitive a downgrade would eventually use.
    const projectsResult = await listProjects();
    if (!projectsResult.ok) {
      return NextResponse.json({ error: projectsResult.error }, { status: 502 });
    }
    const inNamespace = projectsResult.data.filter((p) => p.namespace === org.namespace);
    for (const project of inNamespace) {
      const result = await setProjectTier(project.name, org.namespace, requestedTier);
      if (!result.ok) {
        writeAuditLogEntry({
          timestamp: new Date().toISOString(),
          actor,
          method: "POST",
          path: `/api/orgs/${id}/tier`,
          status: 502,
          requestId,
        });
        return NextResponse.json({ error: result.error }, { status: 502 });
      }
    }
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tier`,
      status: 200,
      requestId,
    });
    return NextResponse.json({
      applied: true,
      tier: requestedTier,
      seatLimit: SEAT_LIMITS[requestedTier],
      requiredApproval: false,
    });
  }

  const approval = await requireApproval({
    action: "tier.downgrade",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedTier },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tier`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tier`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "tier.downgrade requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this downgrade, ` +
          "then retry POST.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists for THIS org's tier.downgrade -- apply
  // the tier that was actually approved (resourcePayload.requestedTier
  // on the approved row), not whatever the caller happens to resend.
  const approvedTier: ProjectTier = approval.approval.resourcePayload?.requestedTier ?? requestedTier;

  const projectsResult = await listProjects();
  if (!projectsResult.ok) {
    return NextResponse.json({ error: projectsResult.error }, { status: 502 });
  }
  const inNamespace = projectsResult.data.filter((p) => p.namespace === org.namespace);
  const patched: string[] = [];
  for (const project of inNamespace) {
    // Only patch Projects actually above the approved tier -- a Project
    // already at or below it is left untouched, so a mixed-tier org
    // never gets a Project silently RAISED by a downgrade action.
    const isStrictlyAbove = tierAtLeast(project.tier, approvedTier) && project.tier !== approvedTier;
    if (!isStrictlyAbove) continue;
    const result = await setProjectTier(project.name, org.namespace, approvedTier);
    if (!result.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/orgs/${id}/tier`,
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    patched.push(project.name);
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/tier`,
    status: 200,
    requestId,
  });
  return NextResponse.json({
    applied: true,
    tier: approvedTier,
    seatLimit: SEAT_LIMITS[approvedTier],
    projectsPatched: patched,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
