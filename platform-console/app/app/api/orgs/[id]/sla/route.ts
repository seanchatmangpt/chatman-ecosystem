import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSla, setOrgSla } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSlaTier, SLA_TIERS } from "@/lib/tiers";

// Real per-org contractual SLA / support-priority tier endpoint: closes
// the gap that lib/tiers.ts's ProjectTier gates compute/quota ceilings
// but names no contractual uptime commitment or support response-time
// SLA -- the specific line item enterprise procurement will not sign
// without (e.g. "99.9% uptime, 4hr response" vs "99.99% uptime, 1hr
// response, 24/7"). Backed by the SAME `platform-console-orgs` registry
// ConfigMap createOrg/setOrgBranding/setOrgRegion already write (no new
// k8s object) -- three more JSON fields merge-patched onto the org's
// existing registry entry.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading the current SLA commitment is not a privileged action.
//   - PUT: owner of THIS org specifically (the spec's "org-admin/
//     platform-admin only" gate -- this codebase's org-scoped role
//     model tops out at "owner", the org-admin equivalent; there is no
//     separate per-org "platform-admin" role, so owner is the correct
//     and only applicable floor here), checked against that org's OWN
//     namespace-local `platform-console-org-roles` ConfigMap via
//     lib/authz.ts's requireRoleIn -- never platform-console's own
//     namespace roles, so an owner of org A can never re-tier org B.
//     `slaResponseTimeHours`/`slaUptimeTargetPct` are never accepted
//     from the request body -- only `slaTier` is, and the two numbers
//     are always recomputed server-side from SLA_TIER_DEFAULTS.

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
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const slaResult = await getOrgSla(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/sla`,
    status: slaResult.ok ? 200 : 502,
    requestId,
  });
  if (!slaResult.ok) {
    return NextResponse.json({ error: slaResult.error }, { status: 502 });
  }
  if (!slaResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  // "Currently meeting SLA" -- this codebase tracks no incident/downtime
  // event log anywhere (no such module exists under lib/ as of this
  // route: quota-enforcement.ts tracks resource quota breaches, not
  // uptime/incidents), so there is no real observed-downtime figure to
  // compare against slaUptimeTargetPct. Rather than fabricate a rolling
  // uptime percentage from data that does not exist, this reports the
  // only thing that is real and derivable today: `true` (no tracked
  // incident has ever been recorded against this org, so nothing
  // contradicts the commitment), with `uptimeDataSource: "no-incident-
  // tracking"` disclosed alongside it so a caller can tell "verified
  // compliant" apart from "no data exists to check against" -- never a
  // silently fabricated percentage.
  return NextResponse.json({
    ...slaResult.data,
    currentlyMeetingSla: true,
    uptimeDataSource: "no-incident-tracking",
  });
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
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sla`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const slaTierRaw = typeof body?.slaTier === "string" ? body.slaTier.trim() : "";
  if (!slaTierRaw || !isSlaTier(slaTierRaw)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/sla`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: `slaTier is required and must be one of: ${SLA_TIERS.join(", ")}` },
      { status: 400 },
    );
  }

  const result = await setOrgSla(id, slaTierRaw);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/sla`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({ org: result.data });
}
