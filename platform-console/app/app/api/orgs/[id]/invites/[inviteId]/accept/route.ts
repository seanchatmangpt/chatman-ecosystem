import { NextRequest, NextResponse } from "next/server";
import { acceptOrgInviteIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real invite acceptance: called post-login by the identity that was
// actually invited (the ONLY auth boundary here -- unlike every other
// org-scoped route in this tree, this is deliberately NOT owner-gated,
// since the whole point is letting a brand-new, not-yet-a-member
// identity redeem a token an owner already minted). lib/authz.ts's
// acceptOrgInviteIn itself re-checks the invite is still pending,
// unexpired, and addressed to this exact identity (case-insensitive)
// before promoting it into a real role entry -- so a mismatched or
// replayed request fails closed with a specific error, not a silent
// no-op or a wrong-identity grant.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; inviteId: string }> },
) {
  const { id, inviteId } = await params;
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

  const result = await acceptOrgInviteIn(namespace, inviteId, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/invites/${inviteId}/accept`,
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ invite: result.data });
}
