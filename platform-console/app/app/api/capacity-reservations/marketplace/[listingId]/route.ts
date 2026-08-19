import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { computeMarketplaceFeeLineItem, MARKETPLACE_FEE_PCT } from "@/lib/invoice-preview";
import { buyResaleListing, getListing } from "@/lib/reservation-marketplace";

// Real single-listing read + buy endpoint for the Reserved-Capacity
// Secondary Marketplace (lib/reservation-marketplace.ts). GET is used by
// a prospective buyer to see one listing's full detail (including its
// real purchase history) before buying; POST performs the real purchase
// -- the two `patchResourceQuotaHard` calls (debit seller, credit buyer)
// this capability's own spec names, plus a platform transaction-fee
// invoice-preview line item (lib/invoice-preview.ts's
// `computeMarketplaceFeeLineItem`).
//
// Auth model:
//   - GET: any authenticated session, same "marketplace listings are
//     platform-wide visible" posture as GET .../marketplace.
//   - POST (buy): owner of the BUYER org specifically (`orgId` in the
//     request body) -- a real spend commitment on that org's behalf,
//     the same "owner required" gate every other billing-mutating route
//     in this tree already uses. The SELLER side of the trade needs no
//     separate authorization here: the seller already authorized giving
//     up this exact capacity when they created the listing (POST
//     .../marketplace, owner-gated at that time).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ listingId: string }> },
) {
  const { listingId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const result = await getListing(listingId);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/capacity-reservations/marketplace/${listingId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "listing not found" }, { status: 404 });
  }
  return NextResponse.json({ listing: result.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ listingId: string }> },
) {
  const { listingId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  const units = typeof body?.units === "number" ? body.units : NaN;

  if (!orgId) {
    return NextResponse.json({ error: "orgId (the buyer org) is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const buyerNamespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, buyerNamespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/capacity-reservations/marketplace/${listingId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await buyResaleListing({
    listingId,
    buyerOrgId: orgId,
    buyerNamespace,
    units,
    purchasedBy: actor,
    platformFeePct: MARKETPLACE_FEE_PCT,
  });

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/capacity-reservations/marketplace/${listingId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  // Real, informational invoice-preview line item for the platform's own
  // transaction fee on this sale -- shown alongside the real purchase
  // record so a buyer sees the total real cost (purchaseAmount + fee) of
  // this trade at the moment it clears, not just the raw resale price.
  const feeLineItem = computeMarketplaceFeeLineItem(
    listingId,
    result.data.listing.sellerOrgId,
    orgId,
    result.data.purchase.purchaseAmount,
    MARKETPLACE_FEE_PCT,
  );

  return NextResponse.json({
    listing: result.data.listing,
    purchase: result.data.purchase,
    invoicePreview: { feeLineItem },
  });
}
