import { NextRequest, NextResponse } from "next/server";
import {
  createOrgInviteIn,
  countUsedSeatsIn,
  listOrgInvitesIn,
  requireRoleIn,
  ROLES,
  roleIdentifierFor,
  type Role,
} from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { tierForNamespace } from "@/lib/overage-billing";
import { SEAT_LIMITS } from "@/lib/tiers";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real seat-based invite endpoint: closes the gap named in this
// control's rationale -- lib/authz.ts's platform-console-org-roles
// ConfigMap let an owner grant a role to any identifier with no cap, no
// pending-invite state, and no tie to the Stripe subscription's tier.
// GET lists every invite (pending/accepted/revoked) plus the real
// seats-used/seats-total pair the seat-usage bar renders. POST creates a
// real pending invite -- but ONLY after checking the real seat count
// (accepted role assignments + still-open pending invites) against
// SEAT_LIMITS[org's real Project tier], the same TIER_RESOURCE_QUOTAS-
// shaped table lib/tiers.ts already establishes for compute quotas, now
// extended to seats.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as branding/ip-allowlist: both verbs
// are owner-of-THIS-org-gated via requireRoleIn against the org's own
// namespace-local ConfigMap -- never the platform's own roles.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/invites`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [invitesResult, tierResult, seatsResult] = await Promise.all([
    listOrgInvitesIn(namespace),
    tierForNamespace(namespace),
    countUsedSeatsIn(namespace),
  ]);

  if (!invitesResult.ok) return NextResponse.json({ error: invitesResult.error }, { status: 502 });
  if (!tierResult.ok) return NextResponse.json({ error: tierResult.error }, { status: 502 });
  if (!seatsResult.ok) return NextResponse.json({ error: seatsResult.error }, { status: 502 });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/invites`,
    status: 200,
    requestId,
  });

  return NextResponse.json({
    invites: invitesResult.data,
    seats: {
      tier: tierResult.data,
      limit: SEAT_LIMITS[tierResult.data],
      used: seatsResult.data.used,
      accepted: seatsResult.data.accepted,
      pending: seatsResult.data.pending,
    },
  });
}

export async function POST(
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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/invites`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const email = typeof body?.email === "string" ? body.email.trim().toLowerCase() : "";
  const role = typeof body?.role === "string" ? (body.role as Role) : ("" as Role);

  if (!EMAIL_RE.test(email) || !ROLES.includes(role)) {
    return NextResponse.json(
      { error: `email must be a valid email address and role must be one of: ${ROLES.join(", ")}` },
      { status: 400 },
    );
  }

  const tierResult = await tierForNamespace(namespace);
  if (!tierResult.ok) return NextResponse.json({ error: tierResult.error }, { status: 502 });

  const seatsResult = await countUsedSeatsIn(namespace);
  if (!seatsResult.ok) return NextResponse.json({ error: seatsResult.error }, { status: 502 });

  const limit = SEAT_LIMITS[tierResult.data];
  const used = seatsResult.data.used;
  if (used >= limit) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/invites`,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      {
        error: "seat limit reached",
        reason: `this org's ${tierResult.data} tier allows ${limit} seats; ${used} are already used (accepted members + pending invites)`,
        seats: { tier: tierResult.data, limit, used, accepted: seatsResult.data.accepted, pending: seatsResult.data.pending },
      },
      { status: 403 },
    );
  }

  const result = await createOrgInviteIn(namespace, { email, role, invitedBy: actor });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/invites`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ invite: result.data });
}
