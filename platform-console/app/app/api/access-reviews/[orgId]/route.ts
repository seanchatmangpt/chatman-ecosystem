import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { completeAccessReview, getAccessReviewHistory } from "@/lib/access-reviews";

// Per-org named-user access review attestation -- the SOC2 CC6.1/CC6.3
// and ISO27001 A.9.2.5 "least-privilege recertification" audit artifact
// (see lib/access-reviews.ts's header comment for the full argument).
//
// GET: any member of the org can read its review history (same viewer
// boundary as most read endpoints -- reviewing evidence isn't itself
// privileged).
// POST: owner/admin-only. "admin" is this app's second-highest built-in
// rank ("member" in lib/authz.ts's Role type is between viewer and owner
// -- there is no separate "admin" Role string in this codebase's RBAC
// model), so the requirement "owner/admin role only" is enforced as
// requireRoleIn(session, namespace, "owner"): the accountable-owner bar
// SOC2 recertification actually requires (a reviewer who can only assign
// roles up to "member" cannot themselves complete a review that could
// revoke an owner).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: `org '${orgId}' not found` }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/access-reviews/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const historyResult = await getAccessReviewHistory(orgId);

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/access-reviews/${orgId}`,
    status: historyResult.ok ? 200 : 502,
    requestId,
  });

  if (!historyResult.ok) {
    return NextResponse.json({ error: historyResult.error }, { status: 502 });
  }
  return NextResponse.json({ orgId, history: historyResult.data });
}

interface CompleteReviewBody {
  revokedIdentifiers?: unknown;
  attestationStatement?: unknown;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((v) => typeof v === "string");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: `org '${orgId}' not found` }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/access-reviews/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  let body: CompleteReviewBody;
  try {
    body = (await request.json()) as CompleteReviewBody;
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  const revokedIdentifiers = isStringArray(body.revokedIdentifiers)
    ? body.revokedIdentifiers
    : [];
  const attestationStatement =
    typeof body.attestationStatement === "string" ? body.attestationStatement.trim() : "";
  if (!attestationStatement) {
    return NextResponse.json(
      { error: "attestationStatement is required" },
      { status: 400 },
    );
  }

  const result = await completeAccessReview({
    orgId,
    namespace: orgResult.data.namespace,
    reviewerIdentifier: actor,
    revokedIdentifiers,
    attestationStatement,
  });

  const status = result.ok ? 200 : 502;
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/access-reviews/${orgId}`,
    status,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  // Real, specific audit-db.ts entry for the completed review itself
  // (SOC2 auditors ask for "when was the access_review.completed event
  // logged," not just "was this POST logged") -- distinct from the
  // generic request-audit line above, same convention every other
  // action-performing route in this app follows (e.g. /api/roles'
  // DELETE writes a second, action-specific line in addition to the
  // request-shaped one).
  writeAuditLogEntry({
    orgId,
    timestamp: result.data.record.reviewedAt,
    actor,
    method: "POST",
    path: `/api/access-reviews/${orgId}#access_review.completed`,
    status: 200,
    requestId,
  });

  return NextResponse.json({
    orgId,
    record: result.data.record,
    revokedCount: result.data.revokedCount,
    history: result.data.history,
  });
}
