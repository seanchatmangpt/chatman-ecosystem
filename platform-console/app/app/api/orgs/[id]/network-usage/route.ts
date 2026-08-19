import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getNamespaceEgressMetrics } from "@/lib/network-usage";
import { computeEgressLineItems, ILLUSTRATIVE_RATES } from "@/lib/invoice-preview";

// Real per-org network-egress metering endpoint -- the read side of the
// same real cross-namespace Istio mesh byte counting
// lib/invoice-preview.ts's getInvoicePreview already folds into
// app/billing/page.tsx, exposed here as its own per-org resource so a
// caller (dashboard widget, FinOps script, a real `pk_live_` Bearer-key
// client) can pull just this org's egress line item without fetching the
// whole compute+egress invoice preview.
//
// `id` resolution follows the exact same convention every other
// `/api/orgs/[id]/*` route in this tree uses (see
// app/api/orgs/[id]/cost-reports/route.ts's own header comment): resolve
// against the real `platform-console-orgs` registry first; when `id`
// doesn't resolve there, `id` is used directly as both the org id AND the
// k8s namespace.
//
// Auth model: any authenticated member of this org (viewer and up) --
// reading this org's own already-visible egress spend is not itself a
// privileged action, same posture as GET /api/orgs/[id]/cost-reports and
// GET /api/orgs/[id]/invoices.
//
// `?window=` a PromQL duration literal for the query window (default
// "1h", matching app/billing/page.tsx's WINDOW_LABEL); `?hours=` the same
// window expressed as a number of hours for the real
// rate-per-hour-times-duration extrapolation lib/network-usage.ts's
// getNamespaceEgressMetrics performs (default 1, matching `window`'s
// default). Both must be supplied together to change the window -- an
// inconsistent pair (e.g. `window=24h` with the default `hours=1`) is the
// caller's own error, same as every other windowLabel/windowHours pair
// this app takes as two independent parameters rather than parsing one
// into the other.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function parseWindowLabel(request: NextRequest): string {
  return request.nextUrl.searchParams.get("window") ?? "1h";
}

function parseWindowHours(request: NextRequest): number {
  const raw = request.nextUrl.searchParams.get("hours");
  if (!raw) return 1;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return 1;
  return Math.min(24 * 31, n);
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
      path: `/api/orgs/${id}/network-usage`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const windowLabel = parseWindowLabel(request);
  const windowHours = parseWindowHours(request);

  const result = await getNamespaceEgressMetrics(namespace, windowLabel, windowHours);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/network-usage`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const [lineItem] = computeEgressLineItems([result.data], ILLUSTRATIVE_RATES);

  return NextResponse.json({
    namespace,
    windowLabel,
    windowHours,
    egressBytes: result.data.egressBytes,
    lineItem,
    rate: ILLUSTRATIVE_RATES.egressPerGb,
    generatedAt: new Date().toISOString(),
  });
}
