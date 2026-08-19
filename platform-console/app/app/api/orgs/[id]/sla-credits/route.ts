import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSla } from "@/lib/orgs";
import { computeCredit, computeMonthlyUptime } from "@/lib/incidents";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real monthly SLA-compliance + service-credit report -- the number
// procurement/legal actually need: real downtime minutes (from
// lib/incidents.ts's Postgres-backed incident ledger, itself derived from
// real Prometheus `up` spans) vs. this org's contracted
// SLA_TIER_DEFAULTS[slaTier].slaUptimeTargetPct, plus the illustrative
// credit owed if missed (lib/incidents.ts's computeCredit -- explicitly
// labeled `illustrative: true`, same convention as
// lib/invoice-preview.ts's ILLUSTRATIVE_RATES). Replaces
// GET /api/orgs/[id]/sla's own `currentlyMeetingSla: true` /
// `uptimeDataSource: "no-incident-tracking"` placeholder for THIS org/
// month with a real computed report -- that route is left unmodified
// (still reports the always-compliant default for callers who only ask
// "what's the current tier", not "did we meet it last month"), this is
// the dedicated endpoint for the real historical answer.
//
// Auth: same "any member of THIS org may read" floor as
// GET /api/orgs/[id]/sla -- an SLA-compliance report is not more
// sensitive than the SLA tier itself, and enterprise buyers reviewing
// their own compliance record need viewer-level access to see it.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const MONTH_RE = /^\d{4}-\d{2}$/;

function currentMonth(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
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
      path: `/api/orgs/${id}/sla-credits`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const { searchParams } = new URL(request.url);
  const month = searchParams.get("month") ?? currentMonth();
  if (!MONTH_RE.test(month)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "month must be 'YYYY-MM'" }, { status: 400 });
  }

  const slaResult = await getOrgSla(id);
  if (!slaResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: slaResult.error }, { status: 502 });
  }
  if (!slaResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const reportResult = await computeMonthlyUptime(id, month, slaResult.data.slaTier);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/sla-credits`,
    status: reportResult.ok ? 200 : 502,
    requestId,
  });
  if (!reportResult.ok) {
    return NextResponse.json({ error: reportResult.error }, { status: 502 });
  }

  const credit = computeCredit(reportResult.data);
  return NextResponse.json({ report: reportResult.data, credit });
}
