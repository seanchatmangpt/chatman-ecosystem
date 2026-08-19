import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { listCostReportSnapshots } from "@/lib/cost-report-history";

// Real cost & usage report snapshot HISTORY endpoint -- the read side of
// the "cost-report-snapshot" lib/scheduled-jobs.ts CronJob command and
// POST /api/internal/cost-report-snapshot: GET lists every previously
// captured snapshot for this org's namespace, oldest first, so
// app/org/cost-reports/page.tsx can render a real trend chart / CSV
// export over time instead of only ever showing today's on-demand
// lib/invoice-preview.ts figure.
//
// `id` resolution follows the exact same convention every other
// `/api/orgs/[id]/*` route in this tree uses (see
// app/api/orgs/[id]/compliance-reports/route.ts's own header comment):
// resolve against the real `platform-console-orgs` registry first; when
// `id` doesn't resolve there, `id` is used directly as both the org id
// AND the k8s namespace -- this deployment's one real single-tenant case
// (`platform-console`).
//
// Auth model: any authenticated member of this org (viewer and up) --
// reading past cost snapshots is not itself a privileged action, same
// posture as branding's/sla's/compliance-reports' GET.

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
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRoleIn(session, namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/cost-reports`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listCostReportSnapshots(namespace);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/cost-reports`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ snapshots: result.data });
}
