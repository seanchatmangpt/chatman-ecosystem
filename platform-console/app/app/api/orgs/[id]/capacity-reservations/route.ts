import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { safeCompareSecret } from "@/lib/s3-export-subscription";
import {
  RESERVATION_TERM_MONTHS,
  isReservationTermMonths,
  reservationDiscountPct,
  type ReservationTermMonths,
} from "@/lib/tiers";
import {
  cancelReservation,
  createReservation,
  getReservation,
  sweepExpiredReservations,
} from "@/lib/capacity-reservations";

// Real Committed-Use Capacity Reservations endpoint (Reserved Capacity
// Tier -- AWS Reserved Instances / GCP Committed Use Discounts
// equivalent): closes the gap that lib/tiers.ts's TIER_RESOURCE_QUOTAS
// only ever sets a fixed per-tier ceiling and lib/overage-billing.ts
// only ever REACTS to usage that bursts past it -- neither lets an org
// commit to and pre-pay for capacity ABOVE their tier's default ceiling
// in exchange for a discount, the forward-commitment line item Fortune 5
// procurement actually budgets against. Backed by the real
// `platform-console-capacity-reservations` ConfigMap
// (lib/capacity-reservations.ts) -- one `reservation.<orgId>` key per org.
//
// `id` resolution follows the exact same convention every other
// `/api/orgs/[id]/*` route in this tree already uses (see
// export-subscription/route.ts's own header comment): resolve against
// the real `platform-console-orgs` registry first; when `id` doesn't
// resolve there, `id` is used directly as both the org id AND the k8s
// namespace.
//
// One reserved id, `_cron`, is NOT a real org -- it is the fan-out
// target the scheduled expiry sweep curls on a recurring schedule (same
// `createCronJob`-pattern shape lib/scheduled-jobs.ts's own
// createExportSubscriptionCronJob/createComplianceReportCronJob already
// establish for a platform-wide or per-org recurring CronJob),
// authenticated by a real shared secret
// (`x-capacity-reservation-cron-secret` matching this pod's own
// `process.env.CAPACITY_RESERVATION_CRON_SECRET`) rather than a session
// cookie -- checked before the session cookie so the CronJob's
// sessionless Pod can reach this route at all, same pattern
// export-subscription/route.ts's own `isCronAuthenticated` already
// establishes. A POST to `/api/orgs/_cron/capacity-reservations` sweeps
// every org's reservation for expiry (sweepExpiredReservations) instead
// of touching any single org's commitment.
//
// Auth model for a real org id:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading the current commitment is not a privileged action.
//   - POST (commit): owner of THIS org specifically -- a real, revenue-
//     bearing forward commitment and an immediate ResourceQuota raise,
//     the same "owner required" gate every other billing/quota-mutating
//     route in this tree (sla, tier, export-subscription) already uses.
//   - DELETE (cancel): owner of THIS org -- reverts the ResourceQuota to
//     the tier default and clears the commitment.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.CAPACITY_RESERVATION_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-capacity-reservation-cron-secret");
  if (!presented) return false;
  return safeCompareSecret(presented, expected);
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();

  if (id === "_cron") {
    return NextResponse.json({ error: "GET is not supported for the cron fan-out target" }, { status: 400 });
  }

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
      path: `/api/orgs/${id}/capacity-reservations`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [reservationResult, tierResult] = await Promise.all([
    getReservation(id),
    getOrgProjectTier(namespace),
  ]);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/capacity-reservations`,
    status: reservationResult.ok && tierResult.ok ? 200 : 502,
    requestId,
  });
  if (!reservationResult.ok) {
    return NextResponse.json({ error: reservationResult.error }, { status: 502 });
  }
  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }

  // Real discount preview for THIS org's own current Project tier, one
  // entry per supported commitment term -- lets the UI show "commit for
  // 12 months at your enterprise tier and save 25%" before the org ever
  // submits a POST, without duplicating RESERVATION_DISCOUNT_TABLE
  // client-side.
  return NextResponse.json({
    reservation: reservationResult.data,
    tier: tierResult.data,
    discountTable: Object.fromEntries(
      RESERVATION_TERM_MONTHS.map((term) => [term, reservationDiscountPct(tierResult.data, term)]),
    ),
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();

  // ---------------------------------------------------- cron fan-out
  if (id === "_cron") {
    if (!isCronAuthenticated(request)) {
      return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
    }
    const result = await sweepExpiredReservations();
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor: "capacity-reservations-cronjob",
      method: "POST",
      path: `/api/orgs/_cron/capacity-reservations`,
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
    return NextResponse.json(result.data);
  }

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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/capacity-reservations`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const committedCpuCores = typeof body?.committedCpuCores === "number" ? body.committedCpuCores : NaN;
  const committedMemoryGi = typeof body?.committedMemoryGi === "number" ? body.committedMemoryGi : NaN;
  const termMonthsRaw = typeof body?.termMonths === "number" ? body.termMonths : NaN;

  if (!Number.isFinite(committedCpuCores) || committedCpuCores <= 0) {
    return NextResponse.json({ error: "committedCpuCores is required and must be a positive number" }, { status: 400 });
  }
  if (!Number.isFinite(committedMemoryGi) || committedMemoryGi <= 0) {
    return NextResponse.json({ error: "committedMemoryGi is required and must be a positive number" }, { status: 400 });
  }
  if (!isReservationTermMonths(termMonthsRaw)) {
    return NextResponse.json(
      { error: `termMonths is required and must be one of: ${RESERVATION_TERM_MONTHS.join(", ")}` },
      { status: 400 },
    );
  }
  const termMonths: ReservationTermMonths = termMonthsRaw;

  const result = await createReservation({
    orgId: id,
    namespace,
    committedCpuCores,
    committedMemoryGi,
    termMonths,
    createdBy: actor,
  });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/capacity-reservations`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ reservation: result.data });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();

  if (id === "_cron") {
    return NextResponse.json({ error: "DELETE is not supported for the cron fan-out target" }, { status: 400 });
  }

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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}/capacity-reservations`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await cancelReservation(id, namespace);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${id}/capacity-reservations`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ cancelled: true });
}
