import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getProject, parseK8sQuantity, patchResourceQuotaHard } from "@/lib/k8s";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { resourceQuotaHardFor } from "@/lib/tiers";
import { checkFreezeGuard } from "@/lib/freeze-windows";
import { listOrgs } from "@/lib/orgs";

// Real maker-checker-gated ResourceQuota override: raising a namespace's
// ResourceQuota ceiling ABOVE its current plan tier's table
// (lib/tiers.ts's TIER_RESOURCE_QUOTAS) is a real, financially-sensitive
// entitlement change -- a customer paying for `pro` getting `enterprise`-
// class ceilings without actually upgrading -- and belongs behind the
// same `quota.override` approval gate app/api/orgs/[id]/route.ts already
// wires for `org.delete`, not a direct patchResourceQuotaHard call.
//
// Flow, same retry-based convention as org.delete:
//   1. Caller must hold role >= owner (same floor the sibling
//      app/api/projects/[name]/tier/route.ts already requires for a
//      tier change -- a quota override is the same class of decision).
//   2. If every requested `spec.hard` value is <= this Project's current
//      tier's ceiling, no approval is needed -- a request that only ever
//      SHRINKS or matches the entitled ceiling is not an override and
//      applies immediately.
//   3. Otherwise requireApproval checks for a fresh (<=24h) approved
//      `quota.override` row for this exact Project name. None exists on
//      the first call -- a pending request (carrying the real requested
//      `spec.hard` map as `resourcePayload.requestedHard`, so an
//      approver can see the real diff, not just an opaque project name)
//      is created and this route returns 202 instead of patching
//      anything.
//   4. A second, distinct owner approves via POST /api/approvals/[id].
//   5. The original caller retries PATCH -- requireApproval now finds
//      the fresh approved row and the real patchResourceQuotaHard runs.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

// The only `spec.hard` keys this console's ResourceQuota objects ever
// set (lib/tiers.ts's resourceQuotaHardFor) -- a request for any other
// key is rejected with a real 400, never silently dropped or forwarded
// to the k8s API as an unvetted PATCH.
const HARD_QUOTA_KEYS = ["pods", "requests.cpu", "requests.memory", "limits.cpu", "limits.memory"] as const;

function parseRequestedHard(body: unknown): Record<string, string> | string {
  if (!body || typeof body !== "object") return "request body must be a JSON object";
  const hard = (body as Record<string, unknown>).hard;
  if (!hard || typeof hard !== "object" || Array.isArray(hard)) {
    return "'hard' is required and must be an object of ResourceQuota spec.hard key/value pairs";
  }
  const entries = Object.entries(hard as Record<string, unknown>);
  if (entries.length === 0) return "'hard' must contain at least one key";
  const result: Record<string, string> = {};
  for (const [key, value] of entries) {
    if (!(HARD_QUOTA_KEYS as readonly string[]).includes(key)) {
      return `unsupported hard quota key '${key}' -- must be one of: ${HARD_QUOTA_KEYS.join(", ")}`;
    }
    if (typeof value !== "string" || value.trim() === "") {
      return `'hard.${key}' must be a non-empty quantity string`;
    }
    if (parseK8sQuantity(value) === null) {
      return `'hard.${key}' is not a valid Kubernetes resource quantity: '${value}'`;
    }
    result[key] = value;
  }
  return result;
}

/** True when every requested value is <= the tier ceiling's same key --
 * missing tier keys are treated as "no ceiling to compare against" only
 * because resourceQuotaHardFor always sets all five keys today; a
 * requested key the tier table doesn't set at all is treated as an
 * override (fail closed, never silently allowed through). */
function exceedsTierCeiling(requestedHard: Record<string, string>, tierHard: Record<string, string>): boolean {
  for (const [key, value] of Object.entries(requestedHard)) {
    const requestedQty = parseK8sQuantity(value);
    const ceilingRaw = tierHard[key];
    const ceilingQty = ceilingRaw !== undefined ? parseK8sQuantity(ceilingRaw) : null;
    if (requestedQty === null || ceilingQty === null || requestedQty > ceilingQty) {
      return true;
    }
  }
  return false;
}

export async function PATCH(
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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/projects/${name}/quota`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const requestedHard = parseRequestedHard(body);
  if (typeof requestedHard === "string") {
    return NextResponse.json({ error: requestedHard }, { status: 400 });
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/projects/${name}/quota`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }
  const project = projectResult.data;

  // Change-freeze guard (lib/freeze-windows.ts, SOC2 CC8 / ITIL change
  // management): resolve the org this Project's namespace belongs to
  // (an org's namespace is 1:1 with its Projects -- same lookup
  // app/api/orgs/[id]/tier/route.ts's sibling uses in reverse) and block
  // ANY quota patch during a declared, active freeze for that org unless
  // a fresh `freeze.override` approval already exists. A Project whose
  // namespace matches no registered org (e.g. the console's own
  // operational "demo-project") has nothing to check against and is
  // never blocked.
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
        method: "PATCH",
        path: `/api/projects/${name}/quota`,
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
                  "patch during the freeze, then retry PATCH.",
              }
            : {}),
        },
        { status: 403 },
      );
    }
  }

  const tierHard = resourceQuotaHardFor(project.tier);

  if (!exceedsTierCeiling(requestedHard, tierHard)) {
    // Not an override -- at or below what this Project's plan tier
    // already entitles it to. Applies immediately, same as any other
    // routine quota patch; no approval trail needed for shrinking or
    // matching the entitled ceiling.
    const result = await patchResourceQuotaHard(project.namespace, `${project.namespace}-quota`, requestedHard);
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/projects/${name}/quota`,
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ applied: true, hard: requestedHard, requiredApproval: false });
  }

  const approval = await requireApproval({
    action: "quota.override",
    targetId: name,
    requestedBy: actor,
    resourcePayload: { requestedHard },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/projects/${name}/quota`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/projects/${name}/quota`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "quota.override requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this override, ` +
          "then retry PATCH.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists for THIS exact Project's quota.override --
  // apply the requested hard limits that were actually approved
  // (resourcePayload.requestedHard on the approved row), not whatever the
  // caller happens to resend, so a retry with a different body after
  // approval can never sneak past the check that was actually signed off.
  const approvedHard = approval.approval.resourcePayload?.requestedHard ?? requestedHard;
  const result = await patchResourceQuotaHard(project.namespace, `${project.namespace}-quota`, approvedHard);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PATCH",
    path: `/api/projects/${name}/quota`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    applied: true,
    hard: approvedHard,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
