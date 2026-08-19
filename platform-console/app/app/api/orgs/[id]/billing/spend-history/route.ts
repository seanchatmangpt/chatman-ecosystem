import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  newRequestId,
  orgSpendHistoryToCsv,
  queryOrgSpendHistory,
  writeAuditLogEntry,
  type SpendHistoryGranularity,
} from "@/lib/audit-db";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { recordExportCustody } from "@/lib/export-custody";

// Real historical spend/usage time series -- the exportable, multi-month
// counterpart to app/billing/page.tsx's point-in-time overage-estimate
// widget. See lib/audit-db.ts's queryOrgSpendHistory for the full method
// (real Stripe Invoice line items + real platform_console.audit_log call
// volume, merged by real timestamp, never fabricated).
//
// Auth: any authenticated member of THIS org (viewer and up) -- same
// floor as GET /api/orgs/[id]/invoices and GET
// /api/orgs/[id]/usage-forecast, both of which this route sits directly
// between: reading this org's own already-visible billing history is not
// a privileged action.
//
// `?granularity=daily|monthly` (default monthly), `?months=` how many
// calendar months back from today the window starts (default 12,
// clamped to [1, 36] -- a FinOps "12 months of spend trend" ask, bounded
// so a client can't request a decade-long Stripe invoices.list scan in
// one call), `?format=csv` returns `text/csv` instead of JSON for direct
// FinOps tooling ingestion (spreadsheet import, chargeback reconciliation
// scripts) -- same data, no client-side reformatting required.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function parseGranularity(request: NextRequest): SpendHistoryGranularity {
  const raw = request.nextUrl.searchParams.get("granularity");
  return raw === "daily" ? "daily" : "monthly";
}

function parseMonths(request: NextRequest): number {
  const raw = request.nextUrl.searchParams.get("months");
  if (!raw) return 12;
  const n = Number(raw);
  if (!Number.isFinite(n)) return 12;
  return Math.min(36, Math.max(1, Math.floor(n)));
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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/billing/spend-history`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const granularity = parseGranularity(request);
  const months = parseMonths(request);
  const format = request.nextUrl.searchParams.get("format") === "csv" ? "csv" : "json";

  const to = new Date();
  const from = new Date(to);
  from.setUTCMonth(from.getUTCMonth() - months);

  const result = await queryOrgSpendHistory(org.id, org.namespace, { from, to, granularity });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/billing/spend-history`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  if (format === "csv") {
    const csv = orgSpendHistoryToCsv(result.data);
    // Real chain-of-custody certificate for this admin's manual bulk CSV
    // pull -- distinct code path from lib/dsar.ts's per-subject export
    // (see lib/export-custody.ts's header comment). Every buckets row in
    // this CSV is one real spend-history record; recordCount is the
    // actual number of data rows (total lines minus the header row), not
    // an estimate. Best-effort: a custody-write failure never blocks the
    // admin's already-generated CSV from downloading.
    const dataRowCount = Math.max(0, csv.split("\n").filter((line) => line.length > 0).length - 1);
    recordExportCustody({
      orgId: id,
      exportedBy: actor,
      recordCount: dataRowCount,
      payload: csv,
      destination: "admin-csv-download",
    }).then((custodyResult) => {
      if (!custodyResult.ok) {
        console.error(
          JSON.stringify({ exportCustodyWriteError: custodyResult.error, orgId: id }),
        );
      }
    });

    return new NextResponse(csv, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${org.id}-spend-history-${granularity}.csv"`,
      },
    });
  }

  return NextResponse.json(result.data);
}
