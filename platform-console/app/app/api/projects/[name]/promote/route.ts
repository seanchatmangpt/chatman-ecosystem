import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getProject, setProjectEnvironment } from "@/lib/k8s";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { isEnvironment, validatePromotion } from "@/lib/environments";
import { checkFreezeGuard } from "@/lib/freeze-windows";
import { listOrgs } from "@/lib/orgs";

// Real, maker-checker-gated environment-promotion pipeline (dev -> staging
// -> prod, SOC2 CC8 change management -- the same control family the
// freeze windows above already enforce): moving a Project's real
// `ENVIRONMENT_LABEL` forward a stage is exactly the "deploy artifact X
// from staging to prod requires a second approver" base compliance
// control Fortune-5 platform procurement checklists require by name.
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Flow, same retry-based convention app/api/projects/[name]/quota/route.ts
// (quota.override) and app/api/projects/[name]/tier/route.ts already
// establish:
//   1. Caller must hold role >= owner -- same floor the sibling tier route
//      already requires for a tier change, a promotion is the same class
//      of decision (what the running Project is entitled to serve real
//      traffic as).
//   2. Only a forward, single-stage move is accepted (lib/environments.ts's
//      validatePromotion): dev -> staging, staging -> prod. Skipping a
//      stage (dev -> prod), reversing, or a no-op is rejected with a real
//      400, never silently coerced.
//   3. Change-freeze guard (lib/freeze-windows.ts, checkFreezeGuard) --
//      the exact same freeze-block pattern already in the sibling
//      quota/tier routes, reused unchanged: any declared, active freeze
//      for the owning org blocks the promotion unless a fresh
//      `freeze.override` approval already exists.
//   4. requireApproval("environment.promote") checks for a fresh (<=24h)
//      approved row for this exact Project name. None exists on the first
//      call -- a pending request (carrying the real fromEnvironment/
//      targetEnvironment as resourcePayload, so an approver can see the
//      real transition, not just an opaque project name) is created and
//      this route returns 202 instead of patching anything.
//   5. A second, distinct owner approves via POST /api/approvals/[id].
//   6. The original caller retries POST -- requireApproval now finds the
//      fresh approved row and the real setProjectEnvironment patch runs.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/promote`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const targetEnvironment =
    typeof (body as Record<string, unknown> | null)?.targetEnvironment === "string"
      ? ((body as Record<string, unknown>).targetEnvironment as string).trim()
      : "";
  if (!targetEnvironment || !isEnvironment(targetEnvironment)) {
    return NextResponse.json(
      { error: `invalid targetEnvironment '${targetEnvironment}' -- must be dev, staging, or prod` },
      { status: 400 },
    );
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/promote`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }
  const project = projectResult.data;
  const fromEnvironment = project.environment;

  const validationError = validatePromotion(fromEnvironment, targetEnvironment);
  if (validationError) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/promote`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  // Change-freeze guard (lib/freeze-windows.ts, SOC2 CC8 / ITIL change
  // management) -- same org-lookup-by-namespace convention the sibling
  // quota and tier routes already use.
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }
  const owningOrg = orgsResult.data.find((o) => o.namespace === project.namespace);
  if (owningOrg) {
    const freezeGuard = await checkFreezeGuard(owningOrg.id, actor);
    if (!freezeGuard.ok) {
      return NextResponse.json({ error: freezeGuard.error }, { status: 502 });
    }
    if (freezeGuard.data.blocked) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/projects/${name}/promote`,
        status: 403,
        requestId,
      });
      return NextResponse.json(
        {
          error: `a declared change-freeze window blocks this action: ${freezeGuard.data.freeze.reason}`,
          freeze: freezeGuard.data.freeze,
          ...(freezeGuard.data.overrideRequest
            ? {
                status: "pending_freeze_override",
                approval: freezeGuard.data.overrideRequest,
                message:
                  "freeze.override requires a second, distinct owner-role approver -- POST /api/approvals/" +
                  `${freezeGuard.data.overrideRequest.requestId} {decision:'approved'} to authorize this ` +
                  "promotion during the freeze, then retry POST.",
              }
            : {}),
        },
        { status: 403 },
      );
    }
  }

  const approval = await requireApproval({
    action: "environment.promote",
    targetId: name,
    requestedBy: actor,
    resourcePayload: { fromEnvironment, targetEnvironment },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/promote`,
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
      path: `/api/projects/${name}/promote`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "environment.promote requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this promotion, ` +
          "then retry POST.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists for THIS exact Project's environment.promote
  // -- apply the transition that was actually approved (resourcePayload on
  // the approved row), not whatever the caller happens to resend, so a
  // retry with a different targetEnvironment after approval can never
  // sneak past the check that was actually signed off.
  const approvedTarget = approval.approval.resourcePayload?.targetEnvironment ?? targetEnvironment;
  const result = await setProjectEnvironment(name, project.namespace, approvedTarget);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/promote`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    project: result.data,
    fromEnvironment,
    targetEnvironment: approvedTarget,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
