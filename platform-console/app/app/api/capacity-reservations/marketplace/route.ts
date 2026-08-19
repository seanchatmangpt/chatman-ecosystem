import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createResaleListing, listListings } from "@/lib/reservation-marketplace";

// Real Reserved-Capacity Secondary Marketplace listing endpoint
// (lib/reservation-marketplace.ts -- see that module's own header
// comment for the full AWS Reserved Instance Marketplace mechanics this
// mirrors: an org lists unused headroom from its own real Committed-Use
// Capacity Reservation, lib/capacity-reservations.ts, for another org to
// buy for the remainder of the term at a real mid-point discount).
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary every other route in this tree uses:
//   - GET: any authenticated session -- browsing what OTHER orgs have
//     listed for resale is the entire point of a marketplace; it must be
//     visible platform-wide, not scoped to one org's own membership. No
//     `orgId` query parameter is required or consulted.
//   - POST (list): owner of the SELLER org specifically (`orgId` in the
//     request body), the same "owner required to touch this org's own
//     revenue-bearing commitment" gate lib/capacity-reservations.ts's
//     own POST route already uses for creating a reservation in the
//     first place.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const result = await listListings();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/capacity-reservations/marketplace",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    listings: [...result.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
  });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  const units = typeof body?.units === "number" ? body.units : NaN;
  const pricePerUnit = typeof body?.pricePerUnit === "number" ? body.pricePerUnit : NaN;

  if (!orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
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
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/capacity-reservations/marketplace",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await createResaleListing({
    sellerOrgId: orgId,
    sellerNamespace: namespace,
    units,
    pricePerUnit,
    createdBy: actor,
  });

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/capacity-reservations/marketplace",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ listing: result.data });
}
